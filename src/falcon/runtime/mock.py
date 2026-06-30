import json

from falcon.core.types import RequestConfig, SimpleResponse
from falcon.runtime.base import ClientRuntime


class MockRuntime(ClientRuntime):
    def __init__(self):
        self.routes: dict[tuple[str, str], SimpleResponse] = {}
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

        self.routes[(method.upper(), url)] = SimpleResponse(
            status_code=status_code,
            headers=headers or {},
            content=content,
            json_data=json_data,
        )

    async def request(self, config: RequestConfig) -> SimpleResponse:
        self.requests.append(config)

        key = (config.method.upper(), config.url)

        if key not in self.routes:
            return SimpleResponse(
                status_code=404,
                headers={},
                content=b'{"detail":"mock response not found"}',
                json_data={"detail": "mock response not found"},
            )

        return self.routes[key]
