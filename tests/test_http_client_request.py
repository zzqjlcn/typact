import asyncio
import inspect
import unittest
from typing import Any

from typact import File, FileData, Form, HttpClient, MockRuntime


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


if __name__ == "__main__":
    unittest.main()
