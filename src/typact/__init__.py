from typact.annotations import Body, Cookie, File, FileData, Form, Header, Path, Query
from typact.builder.request_builder import RequestBuilder
from typact.client.http_client import HttpClient
from typact.converter.response_converter import TypactHttpError, ResponseConverter
from typact.converter.sse_converter import SseResponseConverter
from typact.converter.stream_converter import StreamResponseConverter
from typact.core.errors import TypactNetworkError, TypactTimeoutError
from typact.core.retry import RetryConfig
from typact.core.types import RequestConfig, Response, SimpleResponse
from typact.interceptor.auth import (
    ApiKeyInterceptor,
    BearerTokenInterceptor,
    CallableTokenProvider,
    RefreshableBearerTokenInterceptor,
    TokenProvider,
)
from typact.interceptor.base import InterceptorChain
from typact.interceptor.log import LoggingInterceptor
from typact.interceptor.trace import TraceIdInterceptor
from typact.runtime.base import ClientRuntime
from typact.runtime.mock import MockRuntime
from typact.runtime.urllib import UrllibRuntime

HttpClientError = TypactHttpError

__all__ = [
    "HttpClient",
    "Body",
    "Cookie",
    "File",
    "FileData",
    "Form",
    "Header",
    "Path",
    "Query",
    "ClientRuntime",
    "HttpxRuntime",
    "AioHttpRuntime",
    "UrllibRuntime",
    "MockRuntime",
    "RequestBuilder",
    "ResponseConverter",
    "SseResponseConverter",
    "StreamResponseConverter",
    "TypactHttpError",
    "TypactNetworkError",
    "TypactTimeoutError",
    "RetryConfig",
    "HttpClientError",
    "InterceptorChain",
    "BearerTokenInterceptor",
    "CallableTokenProvider",
    "ApiKeyInterceptor",
    "RefreshableBearerTokenInterceptor",
    "TokenProvider",
    "TraceIdInterceptor",
    "LoggingInterceptor",
    "RequestConfig",
    "Response",
    "SimpleResponse",
    "HttpxClientRuntime",
    "AioHttpClientRuntime",
]


def __getattr__(name: str):
    if name in {"HttpxRuntime", "HttpxClientRuntime"}:
        from typact.runtime.httpx import HttpxRuntime

        return HttpxRuntime

    if name in {"AioHttpRuntime", "AioHttpClientRuntime"}:
        from typact.runtime.aiohttp import AioHttpRuntime

        return AioHttpRuntime

    raise AttributeError(name)
