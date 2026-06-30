from falcon.runtime.base import ClientRuntime
from falcon.runtime.mock import MockRuntime
from falcon.runtime.urllib import UrllibRuntime

__all__ = [
    "ClientRuntime",
    "HttpxRuntime",
    "AioHttpRuntime",
    "UrllibRuntime",
    "MockRuntime",
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
