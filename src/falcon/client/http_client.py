from typing import Any

from falcon.builder.request_builder import RequestBuilder
from falcon.client.decorator import create_route_decorator
from falcon.client.metadata import RouteDefinition
from falcon.converter.response_converter import ResponseConverter
from falcon.interceptor.base import InterceptorChain
from falcon.runtime.base import ClientRuntime
from falcon.runtime.urllib import UrllibRuntime


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
    ):
        self.base_url = base_url
        self.runtime = client_runtime or UrllibRuntime()
        self.request_builder = request_builder or RequestBuilder(
            base_url=base_url,
            default_headers=headers,
        )
        self.response_converter = response_converter or ResponseConverter()
        self.interceptor_chain = interceptor_chain or InterceptorChain()

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

    async def execute(
        self,
        route: RouteDefinition,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ):
        config = self.request_builder.build(route, args, kwargs)
        config = await self.interceptor_chain.apply_request(config)

        response = await self.runtime.request(config)

        if response.status_code == 401:
            retry_config = await self.interceptor_chain.refresh_unauthorized(
                config=config,
                response=response,
            )

            if retry_config is not None:
                response = await self.runtime.request(retry_config)

        response = await self.interceptor_chain.apply_response(response)

        return self.response_converter.convert(
            response=response,
            return_type=route.return_type,
        )

    async def close(self):
        await self.runtime.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
