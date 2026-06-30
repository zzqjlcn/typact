from falcon.client.metadata import RouteDefinition

__all__ = [
    "HttpClient",
    "RouteDefinition",
    "create_route_decorator",
    "run_async_from_sync",
]


def __getattr__(name: str):
    if name in {"HttpClient"}:
        from falcon.client.http_client import HttpClient

        return {"HttpClient": HttpClient}[name]

    if name in {"create_route_decorator", "run_async_from_sync"}:
        from falcon.client.decorator import create_route_decorator, run_async_from_sync

        return {
            "create_route_decorator": create_route_decorator,
            "run_async_from_sync": run_async_from_sync,
        }[name]

    raise AttributeError(name)
