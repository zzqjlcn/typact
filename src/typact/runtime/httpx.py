from typing import Any

from typact.core.types import RequestConfig, Response
from typact.runtime.base import ClientRuntime


class HttpxRuntime(ClientRuntime):
    def __init__(self, client: Any | None = None):
        try:
            import httpx  # type: ignore
        except ImportError as exc:
            raise RuntimeError("请先安装 httpx：pip install 'typact[httpx]'") from exc

        self.client = client or httpx.AsyncClient()

    async def request(self, config: RequestConfig) -> Response:
        response = await self.client.request(
            method=config.method,
            url=config.url,
            params=config.params,
            headers=config.headers,
            cookies=config.cookies,
            json=config.json,
            data=config.data,
            files=config.files,
        )

        json_data = None

        if response.content:
            try:
                json_data = response.json()
            except Exception:
                json_data = None

        return Response(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            json_data=json_data,
        )

    async def close(self) -> None:
        await self.client.aclose()
