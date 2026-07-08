from falcon.annotations import Body, Cookie, File, Form, Header, Path, Query
from falcon.builder.request_builder import RequestBuilder
from falcon.client.http_client import HttpClient
from falcon.converter.response_converter import FalconHttpError, ResponseConverter
from falcon.core.types import RequestConfig, SimpleResponse
from falcon.interceptor.auth import (
    ApiKeyInterceptor,
    BearerTokenInterceptor,
    CallableTokenProvider,
    RefreshableBearerTokenInterceptor,
    TokenProvider,
)
from falcon.interceptor.base import InterceptorChain
from falcon.interceptor.log import LoggingInterceptor
from falcon.interceptor.trace import TraceIdInterceptor
from falcon.runtime.base import ClientRuntime
from falcon.runtime.mock import MockRuntime
from falcon.runtime.urllib import UrllibRuntime

HttpClientError = FalconHttpError

__all__ = [
    "HttpClient",
    "Body",
    "Cookie",
    "File",
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
    "FalconHttpError",
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
    "SimpleResponse",
    "HttpxClientRuntime",
    "AioHttpClientRuntime",
]


def __getattr__(name: str):
    if name in {"HttpxRuntime", "HttpxClientRuntime"}:
        from falcon.runtime.httpx import HttpxRuntime

        return HttpxRuntime

    if name in {"AioHttpRuntime", "AioHttpClientRuntime"}:
        from falcon.runtime.aiohttp import AioHttpRuntime

        return AioHttpRuntime

    raise AttributeError(name)
