import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Protocol

from typact.core.types import RequestConfig, Response


class TokenProvider(Protocol):
    async def get_token(self) -> str: ...

    async def refresh_token(self) -> str: ...


class CallableTokenProvider:
    def __init__(
        self,
        refresh: Callable[[], str | Awaitable[str]],
        *,
        token: str | None = None,
    ):
        self.refresh = refresh
        self.token = token
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        if self.token is None:
            return await self.refresh_token()
        return self.token

    async def refresh_token(self) -> str:
        async with self._lock:
            token = self.refresh()

            if inspect.isawaitable(token):
                token = await token

            self.token = str(token).strip()
            return self.token


class BearerTokenInterceptor:
    def __init__(self, token: str):
        self.token = token

    async def before_request(self, config: RequestConfig) -> RequestConfig:
        config.headers["Authorization"] = f"Bearer {self.token}"
        return config


class RefreshableBearerTokenInterceptor:
    def __init__(
        self,
        token_provider: TokenProvider,
        *,
        header_name: str = "Authorization",
        scheme: str | None = "Bearer",
        retry_on_unauthorized: bool = True,
    ):
        self.token_provider = token_provider
        self.header_name = header_name
        self.scheme = scheme
        self.retry_on_unauthorized = retry_on_unauthorized

    async def before_request(self, config: RequestConfig) -> RequestConfig:
        token = await self.token_provider.get_token()
        config.headers[self.header_name] = self._format_token(token)
        return config

    async def refresh_on_unauthorized(
        self,
        config: RequestConfig,
        response: Response,
    ) -> RequestConfig | None:
        if not self.retry_on_unauthorized or response.status_code != 401:
            return None

        token = await self.token_provider.refresh_token()
        config.headers[self.header_name] = self._format_token(token)
        return config

    def _format_token(self, token: str) -> str:
        token = token.strip()

        if self.scheme is None:
            return token
        return f"{self.scheme} {token}"


class ApiKeyInterceptor:
    def __init__(
        self,
        api_key: str,
        header_name: str = "X-API-Key",
    ):
        self.api_key = api_key
        self.header_name = header_name

    async def before_request(self, config: RequestConfig) -> RequestConfig:
        config.headers[self.header_name] = self.api_key
        return config
