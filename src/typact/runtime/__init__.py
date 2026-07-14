from typact.runtime.base import ClientRuntime
from typact.runtime.mock import MockRuntime
from typact.runtime.urllib import UrllibRuntime

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
        from typact.runtime.httpx import HttpxRuntime

        return HttpxRuntime

    if name in {"AioHttpRuntime", "AioHttpClientRuntime"}:
        from typact.runtime.aiohttp import AioHttpRuntime

        return AioHttpRuntime

    raise AttributeError(name)
