import asyncio
import inspect
import threading
from functools import wraps
from typing import Any, Callable, get_type_hints

from typact.client.metadata import RouteDefinition


def run_async_from_sync(coro_factory: Callable[[], Any]):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro_factory())

    result: list[Any] = []
    error: list[BaseException] = []

    def target():
        try:
            result.append(asyncio.run(coro_factory()))
        except BaseException as exc:
            error.append(exc)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()

    if error:
        raise error[0]

    return result[0]


def create_route_decorator(client: Any, method: str, path: str):
    def decorator(func: Callable):
        route = RouteDefinition(
            method=method,
            path=path,
            signature=inspect.signature(func),
            return_type=get_type_hints(func).get("return", Any),
            is_async=inspect.iscoroutinefunction(func),
        )

        if route.is_async:

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await client.execute(route, args, kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            async def coro():
                return await client.execute(route, args, kwargs)

            return run_async_from_sync(coro)

        return sync_wrapper

    return decorator
