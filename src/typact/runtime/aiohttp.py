from typing import Any

from typact.core.errors import TypactHttpError
from typact.core.types import RequestConfig, Response
from typact.runtime.base import ClientRuntime


class AioHttpRuntime(ClientRuntime):
    def __init__(self, session: Any | None = None):
        try:
            import aiohttp  # type: ignore
        except ImportError as exc:
            raise RuntimeError("请先安装 aiohttp：pip install 'typact[aiohttp]'") from exc

        self._aiohttp = aiohttp
        self.session = session
        self._own_session = session is None

    async def _get_session(self):
        if self.session is None:
            self.session = self._aiohttp.ClientSession()
        return self.session

    async def request(self, config: RequestConfig) -> Response:
        session = await self._get_session()

        async with session.request(
            method=config.method,
            url=config.url,
            params=config.params,
            headers=config.headers,
            cookies=config.cookies,
            json=config.json,
            data=config.data,
            timeout=config.timeout,
        ) as response:
            content = await response.read()

            json_data = None

            if content:
                try:
                    json_data = await response.json()
                except Exception:
                    json_data = None

            return Response(
                status_code=response.status,
                headers=dict(response.headers),
                content=content,
                json_data=json_data,
            )

    async def close(self) -> None:
        if self._own_session and self.session is not None:
            await self.session.close()

    def stream(self, config: RequestConfig):
        async def iterator():
            session = await self._get_session()
            async with session.request(
                method=config.method,
                url=config.url,
                params=config.params,
                headers=config.headers,
                cookies=config.cookies,
                json=config.json,
                data=config.data,
                timeout=config.timeout,
            ) as response:
                if response.status >= 400:
                    raise TypactHttpError(response.status, await response.read())

                async for chunk in response.content.iter_any():
                    yield chunk

        return iterator()
