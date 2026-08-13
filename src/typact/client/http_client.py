import asyncio
import inspect
from collections.abc import Callable, Sequence
from typing import Any, ParamSpec, TypeVar, overload

from typact.builder.request_builder import RequestBuilder
from typact.client.decorator import create_route_decorator
from typact.client.metadata import RouteDefinition
from typact.converter.response_converter import ResponseConverter
from typact.core.errors import TypactNetworkError, TypactTimeoutError
from typact.core.retry import RetryConfig
from typact.core.types import RequestConfig, Response
from typact.interceptor.base import InterceptorChain
from typact.runtime.base import ClientRuntime
from typact.runtime.urllib import UrllibRuntime

P = ParamSpec("P")
R = TypeVar("R")


class HttpClient:
    def __init__(
        self,
        base_url: str,
        *,
        client_runtime: ClientRuntime | None = None,
        headers: dict[str, str] | None = None,
        request_builder: RequestBuilder | None = None,
        response_converter: ResponseConverter | None = None,
        interceptor_chain: InterceptorChain | None = None,
        timeout: float | None = None,
        retry_config: RetryConfig | None = None,
    ):
        self.base_url = base_url
        self.runtime = client_runtime or UrllibRuntime()
        self.request_builder = request_builder or RequestBuilder(
            base_url=base_url,
            default_headers=headers,
        )
        self.response_converter = response_converter or ResponseConverter()
        self.interceptor_chain = interceptor_chain or InterceptorChain()
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()

    def get(self, path: str):
        return create_route_decorator(self, "GET", path)

    def post(self, path: str):
        return create_route_decorator(self, "POST", path)

    def put(self, path: str):
        return create_route_decorator(self, "PUT", path)

    def patch(self, path: str):
        return create_route_decorator(self, "PATCH", path)

    def delete(self, path: str):
        return create_route_decorator(self, "DELETE", path)

    @overload
    def request(
        self,
        path: str,
        *,
        method: str,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

    @overload
    def request(
        self,
        path: str,
        func: Callable[P, R],
        *,
        methods: Sequence[str],
    ) -> Callable[P, R]: ...

    def request(
        self,
        path: str,
        func: Callable[P, R] | None = None,
        *,
        method: str | None = None,
        methods: Sequence[str] | None = None,
    ):
        if method is not None and methods is not None:
            raise TypeError("method and methods cannot be used together")

        route_methods = [method] if method is not None else list(methods or ())
        if len(route_methods) != 1:
            raise ValueError("request requires exactly one HTTP method")

        decorator = create_route_decorator(self, route_methods[0], path)

        def register(route_func: Callable[P, R]) -> Callable[P, R]:
            wrapper = decorator(route_func)

            if inspect.ismethod(route_func) and route_func.__self__ is not None:
                setattr(route_func.__self__, route_func.__name__, wrapper)

            return wrapper

        if func is None:
            return register

        return register(func)

    async def execute(
        self,
        route: RouteDefinition,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ):
        config = self.request_builder.build(route, args, kwargs)
        config.timeout = self.timeout
        config = await self.interceptor_chain.apply_request(config)

        response = await self._request_with_retry(config)

        if response.status_code == 401:
            retry_config = await self.interceptor_chain.refresh_unauthorized(
                config=config,
                response=response,
            )

            if retry_config is not None:
                response = await self._request_with_retry(retry_config)

        response = await self.interceptor_chain.apply_response(response)

        return self.response_converter.convert(
            response=response,
            return_type=route.return_type,
        )

    async def close(self):
        await self.runtime.close()

    async def _request_with_retry(self, config: RequestConfig) -> Response:
        retry_number = 0

        while True:
            try:
                response = await self._request_once(config)
            except Exception as exc:
                if not self._is_network_error(exc):
                    raise

                if not self._can_retry(config, retry_number):
                    if isinstance(exc, TypactTimeoutError):
                        raise exc
                    if isinstance(exc, TimeoutError):
                        raise TypactTimeoutError(config.timeout or 0) from exc
                    raise TypactNetworkError("Typact request failed due to a network error", cause=exc) from exc
            else:
                if (
                    response.status_code not in self.retry_config.retry_status_codes
                    or not self._can_retry(config, retry_number)
                ):
                    return response

            await asyncio.sleep(self.retry_config.delay_for_retry(retry_number))
            retry_number += 1

    async def _request_once(self, config: RequestConfig) -> Response:
        if config.timeout is None:
            return await self.runtime.request(config)

        try:
            async with asyncio.timeout(config.timeout):
                return await self.runtime.request(config)
        except TimeoutError as exc:
            raise TypactTimeoutError(config.timeout) from exc

    def _can_retry(self, config: RequestConfig, retry_number: int) -> bool:
        return (
            retry_number < self.retry_config.max_retries
            and self.retry_config.allows_method(config.method)
        )

    @staticmethod
    def _is_network_error(exc: Exception) -> bool:
        if isinstance(exc, TypactTimeoutError):
            return True
        if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
            return True
        return exc.__class__.__module__.startswith(("aiohttp", "httpx", "urllib"))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
