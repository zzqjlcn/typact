import json

from typact.core.types import RequestConfig, Response
from typact.runtime.base import ClientRuntime


class MockRuntime(ClientRuntime):
    def __init__(self):
        self.routes: dict[tuple[str, str], Response] = {}
        self.response_queues: dict[tuple[str, str], list[Response]] = {}
        self.requests: list[RequestConfig] = []

    def add_response(
        self,
        method: str,
        url: str,
        *,
        status_code: int = 200,
        json_data=None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ):
        if content is None:
            content = (
                json.dumps(json_data).encode("utf-8")
                if json_data is not None
                else b""
            )

        self.routes[(method.upper(), url)] = Response(
            status_code=status_code,
            headers=headers or {},
            content=content,
            json_data=json_data,
        )

    def add_responses(
        self,
        method: str,
        url: str,
        responses: list[Response],
    ):
        self.response_queues[(method.upper(), url)] = responses

    async def request(self, config: RequestConfig) -> Response:
        self.requests.append(self._snapshot_config(config))

        key = (config.method.upper(), config.url)

        if key in self.response_queues and self.response_queues[key]:
            return self.response_queues[key].pop(0)

        if key not in self.routes:
            return Response(
                status_code=404,
                headers={},
                content=b'{"detail":"mock response not found"}',
                json_data={"detail": "mock response not found"},
            )

        return self.routes[key]

    @staticmethod
    def _snapshot_config(config: RequestConfig) -> RequestConfig:
        return RequestConfig(
            method=config.method,
            url=config.url,
            params=dict(config.params or {}),
            headers=dict(config.headers or {}),
            cookies=dict(config.cookies or {}),
            json=config.json,
            data=config.data,
            files=dict(config.files) if isinstance(config.files, dict) else config.files,
        )
