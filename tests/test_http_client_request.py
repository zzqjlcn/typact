import asyncio
import inspect
import unittest
from typing import Any

from typact import (
    File,
    FileData,
    Form,
    HttpClient,
    MockRuntime,
    Response,
    RetryConfig,
    TypactHttpError,
    TypactNetworkError,
    TypactTimeoutError,
)
from typact.core.types import RequestConfig
from typact.runtime.base import ClientRuntime


class FlakyRuntime(ClientRuntime):
    def __init__(self, failures: int):
        self.failures = failures
        self.requests: list[RequestConfig] = []

    async def request(self, config: RequestConfig) -> Response:
        self.requests.append(config)
        if self.failures:
            self.failures -= 1
            raise ConnectionError("connection refused")
        return Response(status_code=200, headers={}, content=b'{"ok": true}', json_data={"ok": True})


class SlowRuntime(ClientRuntime):
    async def request(self, config: RequestConfig) -> Response:
        await asyncio.sleep(1)
        return Response(status_code=200, headers={}, content=b"{}", json_data={})


class LoginApi:
    def __init__(self, runtime: MockRuntime):
        self.client = HttpClient("https://example.test", client_runtime=runtime)
        self.client.request("/auth/login", method="POST")(self.login)

    async def login(
        self,
        name: str = Form(),
        password: str = Form(),
    ) -> dict[str, Any]:
        raise NotImplementedError


class DirectLoginApi:
    def __init__(self, runtime: MockRuntime):
        self.client = HttpClient("https://example.test", client_runtime=runtime)
        self.client.request("/auth/login", self.login, methods=["POST"])

    async def login(
        self,
        name: str = Form(),
        password: str = Form(),
    ) -> dict[str, Any]:
        raise NotImplementedError


class UploadApi:
    def __init__(self, runtime: MockRuntime):
        self.client = HttpClient("https://example.test", client_runtime=runtime)
        self.client.request("/upload", method="POST")(self.upload)

    async def upload(
        self,
        attachment: FileData = File(alias="file"),
        raw: bytes = File(),
    ) -> dict[str, Any]:
        raise NotImplementedError


class DownloadApi:
    def __init__(self, runtime: MockRuntime):
        self.client = HttpClient("https://example.test", client_runtime=runtime)
        self.client.request("/download", method="GET")(self.download)
        self.client.request("/download-response", method="GET")(self.download_response)

    async def download(self) -> bytes:
        raise NotImplementedError

    async def download_response(self) -> Response:
        raise NotImplementedError


class RetryApi:
    def __init__(self, client: HttpClient):
        client.request("/health", method="GET")(self.health)
        client.request("/events", method="POST")(self.create_event)

    async def health(self) -> dict:
        raise NotImplementedError

    async def create_event(self) -> dict:
        raise NotImplementedError


class HttpClientRequestTest(unittest.TestCase):
    def test_registers_bound_method_and_preserves_signature(self):
        runtime = MockRuntime()
        runtime.add_response(
            "POST",
            "https://example.test/auth/login",
            json_data={"token": "secret"},
        )
        api = LoginApi(runtime)

        result = asyncio.run(api.login("alice", "password"))

        self.assertEqual(result, {"token": "secret"})
        self.assertEqual(runtime.requests[0].data, {"name": "alice", "password": "password"})
        self.assertEqual(list(inspect.signature(api.login).parameters), ["name", "password"])

    def test_supports_direct_callable_form(self):
        runtime = MockRuntime()
        runtime.add_response(
            "POST",
            "https://example.test/auth/login",
            json_data={"ok": True},
        )
        api = DirectLoginApi(runtime)

        result = asyncio.run(api.login(name="alice", password="password"))

        self.assertEqual(result, {"ok": True})
        self.assertEqual(runtime.requests[0].method, "POST")

    def test_builds_file_data_and_preserves_bytes(self):
        runtime = MockRuntime()
        runtime.add_response(
            "POST",
            "https://example.test/upload",
            json_data={"ok": True},
        )
        api = UploadApi(runtime)

        result = asyncio.run(
            api.upload(
                FileData(
                    content=b"report",
                    filename="report.txt",
                    content_type="text/plain",
                ),
                b"raw content",
            )
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(
            runtime.requests[0].files,
            {
                "file": ("report.txt", b"report", "text/plain"),
                "raw": b"raw content",
            },
        )

    def test_returns_raw_bytes_from_download(self):
        runtime = MockRuntime()
        runtime.add_response(
            "GET",
            "https://example.test/download",
            content=b"\x00\x01typact\xff",
        )
        api = DownloadApi(runtime)

        result = asyncio.run(api.download())

        self.assertEqual(result, b"\x00\x01typact\xff")

    def test_returns_empty_bytes_from_download(self):
        runtime = MockRuntime()
        runtime.add_response(
            "GET",
            "https://example.test/download",
            content=b"",
        )
        api = DownloadApi(runtime)

        result = asyncio.run(api.download())

        self.assertEqual(result, b"")

    def test_returns_typact_response_for_error_status(self):
        runtime = MockRuntime()
        runtime.add_response(
            "GET",
            "https://example.test/download-response",
            status_code=404,
            json_data={"detail": "not found"},
            headers={"X-Request-Id": "request-id"},
        )
        api = DownloadApi(runtime)

        result = asyncio.run(api.download_response())

        self.assertIsInstance(result, Response)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.headers["X-Request-Id"], "request-id")
        self.assertEqual(result.content, b'{"detail": "not found"}')
        self.assertEqual(result.text, '{"detail": "not found"}')
        self.assertEqual(result.json(), {"detail": "not found"})

    def test_retries_retryable_status_for_idempotent_request(self):
        runtime = MockRuntime()
        runtime.add_responses(
            "GET",
            "https://example.test/health",
            [
                Response(status_code=503, headers={}, content=b"{}", json_data={}),
                Response(status_code=200, headers={}, content=b'{"ok": true}', json_data={"ok": True}),
            ],
        )
        api = RetryApi(
            HttpClient(
                "https://example.test",
                client_runtime=runtime,
                retry_config=RetryConfig(max_retries=1, initial_delay=0),
            )
        )

        self.assertEqual(asyncio.run(api.health()), {"ok": True})
        self.assertEqual(len(runtime.requests), 2)

    def test_does_not_retry_post_by_default(self):
        runtime = MockRuntime()
        runtime.add_response("POST", "https://example.test/events", status_code=503)
        api = RetryApi(
            HttpClient(
                "https://example.test",
                client_runtime=runtime,
                retry_config=RetryConfig(max_retries=1, initial_delay=0),
            )
        )

        with self.assertRaises(TypactHttpError):
            asyncio.run(api.create_event())
        self.assertEqual(len(runtime.requests), 1)

    def test_retries_network_error(self):
        runtime = FlakyRuntime(failures=1)
        api = RetryApi(
            HttpClient(
                "https://example.test",
                client_runtime=runtime,
                retry_config=RetryConfig(max_retries=1, initial_delay=0),
            )
        )

        self.assertEqual(asyncio.run(api.health()), {"ok": True})
        self.assertEqual(len(runtime.requests), 2)

    def test_wraps_network_error_after_retries_are_exhausted(self):
        api = RetryApi(HttpClient("https://example.test", client_runtime=FlakyRuntime(failures=1)))

        with self.assertRaises(TypactNetworkError):
            asyncio.run(api.health())

    def test_raises_timeout_error(self):
        api = RetryApi(HttpClient("https://example.test", client_runtime=SlowRuntime(), timeout=0.01))

        with self.assertRaises(TypactTimeoutError):
            asyncio.run(api.health())


if __name__ == "__main__":
    unittest.main()
