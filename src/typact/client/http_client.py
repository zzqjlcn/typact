import asyncio
import inspect
from collections.abc import AsyncIterator
from collections.abc import Callable, Sequence
from typing import Any, ParamSpec, TypeVar, overload

from typact.builder.request_builder import RequestBuilder
from typact.client.decorator import create_route_decorator
from typact.client.metadata import UNSET, RouteDefinition
from typact.converter.response_converter import ResponseConverter
from typact.converter.sse_converter import SseResponseConverter
from typact.converter.stream_converter import StreamResponseConverter
from typact.core.errors import TypactHttpError, TypactNetworkError, TypactTimeoutError
from typact.core.events import RequestEvent, RequestEventHandler, RequestEventPhase
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
        event_handlers: Sequence[RequestEventHandler] | None = None,
    ):
        self.base_url = base_url
        self.runtime = client_runtime or UrllibRuntime()
        self.request_builder = request_builder or RequestBuilder(
            base_url=base_url,
            default_headers=headers,
        )
        self.response_converter = response_converter or ResponseConverter()
        self.sse_converter = SseResponseConverter()
        self.stream_converter = StreamResponseConverter()
        self.interceptor_chain = interceptor_chain or InterceptorChain()
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than 0")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.event_handlers = list(event_handlers or ())

    def add_event_handler(self, handler: RequestEventHandler) -> None:
        self.event_handlers.append(handler)

    def get(
        self,
        path: str,
        *,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ):
        return create_route_decorator(
            self,
            "GET",
            path,
            timeout=timeout,
            retry_config=retry_config,
        )

    def post(
        self,
        path: str,
        *,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ):
        return create_route_decorator(
            self,
            "POST",
            path,
            timeout=timeout,
            retry_config=retry_config,
        )

    def put(
        self,
        path: str,
        *,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ):
        return create_route_decorator(
            self,
            "PUT",
            path,
            timeout=timeout,
            retry_config=retry_config,
        )

    def patch(
        self,
        path: str,
        *,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ):
        return create_route_decorator(
            self,
            "PATCH",
            path,
            timeout=timeout,
            retry_config=retry_config,
        )

    def delete(
        self,
        path: str,
        *,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ):
        return create_route_decorator(
            self,
            "DELETE",
            path,
            timeout=timeout,
            retry_config=retry_config,
        )

    @overload
    def request(
        self,
        path: str,
        *,
        method: str,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

    @overload
    def request(
        self,
        path: str,
        func: Callable[P, R],
        *,
        methods: Sequence[str],
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ) -> Callable[P, R]: ...

    def request(
        self,
        path: str,
        func: Callable[P, R] | None = None,
        *,
        method: str | None = None,
        methods: Sequence[str] | None = None,
        timeout: float | None | object = UNSET,
        retry_config: RetryConfig | None | object = UNSET,
    ):
        if method is not None and methods is not None:
            raise TypeError("method and methods cannot be used together")

        route_methods = [method] if method is not None else list(methods or ())
        if len(route_methods) != 1:
            raise ValueError("request requires exactly one HTTP method")

        decorator = create_route_decorator(
            self,
            route_methods[0],
            path,
            timeout=timeout,
            retry_config=retry_config,
        )

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
        config = self._build_request_config(route, args, kwargs)
        config = await self.interceptor_chain.apply_request(config)
        await self._emit_event("request", config, attempt=1)

        try:
            retry_config = self._get_retry_config(route)
            response, attempt = await self._request_with_retry(config, retry_config)

            if response.status_code == 401:
                refreshed_config = await self.interceptor_chain.refresh_unauthorized(
                    config=config,
                    response=response,
                )

                if refreshed_config is not None:
                    config = refreshed_config
                    await self._emit_event(
                        "retry",
                        config,
                        attempt=attempt + 1,
                        response=response,
                    )
                    response, refresh_attempt = await self._request_with_retry(
                        config,
                        retry_config,
                    )
                    attempt += refresh_attempt

            response = await self.interceptor_chain.apply_response(response)
            await self._emit_event("response", config, attempt=attempt, response=response)

            return self.response_converter.convert(
                response=response,
                return_type=route.return_type,
            )
        except Exception as exc:
            await self._emit_event("failure", config, attempt=1, error=exc)
            raise

    async def close(self):
        await self.runtime.close()

    async def execute_stream(
        self,
        route: RouteDefinition,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncIterator[Any]:
        config = self._build_request_config(route, args, kwargs)
        config = await self.interceptor_chain.apply_request(config)
        await self._emit_event("request", config, attempt=1)
        item_type = route.return_type.__args__[0]
        retry_config = self._get_retry_config(route)

        converter = (
            self.stream_converter
            if item_type in {bytes, str}
            else self.sse_converter
        )

        try:
            async for item in converter.convert(
                self._stream_with_retry(config, retry_config),
                item_type,
            ):
                yield item
        except Exception as exc:
            await self._emit_event("failure", config, attempt=1, error=exc)
            raise

    def _build_request_config(
        self,
        route: RouteDefinition,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> RequestConfig:
        config = self.request_builder.build(route, args, kwargs)
        config.timeout = self.timeout if route.timeout is UNSET else route.timeout
        return config

    def _get_retry_config(self, route: RouteDefinition) -> RetryConfig:
        if route.retry_config is UNSET:
            return self.retry_config
        return route.retry_config or RetryConfig()

    async def _request_with_retry(
        self,
        config: RequestConfig,
        retry_config: RetryConfig,
    ) -> tuple[Response, int]:
        retry_number = 0

        while True:
            response: Response | None = None
            error: Exception | None = None

            try:
                response = await self._request_once(config)
            except Exception as exc:
                error = exc
                if not self._is_network_error(exc):
                    raise

                if not self._can_retry(config, retry_number, retry_config):
                    if isinstance(exc, TypactTimeoutError):
                        raise exc
                    if isinstance(exc, TimeoutError):
                        raise TypactTimeoutError(config.timeout or 0) from exc
                    raise TypactNetworkError("Typact request failed due to a network error", cause=exc) from exc
            else:
                if (
                    not self._can_retry(config, retry_number, retry_config)
                    or not retry_config.matches_response(response)
                ):
                    return response, retry_number + 1

            await self._emit_event(
                "retry",
                config,
                attempt=retry_number + 2,
                response=response,
                error=error,
            )
            await asyncio.sleep(retry_config.delay_for_retry(retry_number))
            retry_number += 1

    async def _request_once(self, config: RequestConfig) -> Response:
        if config.timeout is None:
            return await self.runtime.request(config)

        try:
            return await asyncio.wait_for(
                self.runtime.request(config),
                timeout=config.timeout,
            )
        except asyncio.TimeoutError as exc:
            raise TypactTimeoutError(config.timeout) from exc

    async def _stream_with_retry(
        self,
        config: RequestConfig,
        retry_config: RetryConfig,
    ) -> AsyncIterator[bytes]:
        if retry_config.should_retry_response is not None:
            raise ValueError(
                "should_retry_response is not supported for streaming requests; "
                "set a route-level retry_config using retry_status_codes or None"
            )
        retry_number = 0

        while True:
            received_chunk = False
            emitted_response = False
            error: Exception | None = None

            try:
                async for chunk in self.runtime.stream(config):
                    received_chunk = True
                    if not emitted_response:
                        await self._emit_event(
                            "response",
                            config,
                            attempt=retry_number + 1,
                        )
                        emitted_response = True
                    yield chunk
                if not emitted_response:
                    await self._emit_event(
                        "response",
                        config,
                        attempt=retry_number + 1,
                    )
                return
            except Exception as exc:
                error = exc
                can_retry = (
                    not received_chunk
                    and self._can_retry(config, retry_number, retry_config)
                    and self._is_retryable_stream_error(exc, retry_config)
                )
                if not can_retry:
                    raise

            await self._emit_event(
                "retry",
                config,
                attempt=retry_number + 2,
                error=error,
            )
            await asyncio.sleep(retry_config.delay_for_retry(retry_number))
            retry_number += 1

    async def _emit_event(
        self,
        phase: RequestEventPhase,
        config: RequestConfig,
        *,
        attempt: int,
        response: Response | None = None,
        error: Exception | None = None,
    ) -> None:
        event = RequestEvent(
            phase=phase,
            config=config,
            attempt=attempt,
            response=response,
            error=error,
        )
        for handler in self.event_handlers:
            result = handler(event)
            if inspect.isawaitable(result):
                await result

    def _can_retry(
        self,
        config: RequestConfig,
        retry_number: int,
        retry_config: RetryConfig,
    ) -> bool:
        return (
            retry_number < retry_config.max_retries
            and retry_config.allows_method(config.method)
        )

    def _is_retryable_stream_error(self, exc: Exception, retry_config: RetryConfig) -> bool:
        if isinstance(exc, TypactHttpError):
            return exc.status_code in (retry_config.retry_status_codes or ())
        return self._is_network_error(exc)

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
