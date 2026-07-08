from typing import Protocol

from falcon.core.types import RequestConfig, SimpleResponse


class RequestInterceptor(Protocol):
    async def before_request(self, config: RequestConfig) -> RequestConfig:
        ...


class ResponseInterceptor(Protocol):
    async def after_response(self, response: SimpleResponse) -> SimpleResponse:
        ...


class InterceptorChain:
    def __init__(
        self,
        request_interceptors: list[RequestInterceptor] | None = None,
        response_interceptors: list[ResponseInterceptor] | None = None,
    ):
        self.request_interceptors = request_interceptors or []
        self.response_interceptors = response_interceptors or []

    async def apply_request(self, config: RequestConfig) -> RequestConfig:
        for interceptor in self.request_interceptors:
            config = await interceptor.before_request(config)
        return config

    async def apply_response(self, response: SimpleResponse) -> SimpleResponse:
        for interceptor in self.response_interceptors:
            response = await interceptor.after_response(response)
        return response

    async def refresh_unauthorized(
        self,
        config: RequestConfig,
        response: SimpleResponse,
    ) -> RequestConfig | None:
        for interceptor in self.request_interceptors:
            refresh = getattr(interceptor, "refresh_on_unauthorized", None)

            if refresh is None:
                continue

            refreshed_config = await refresh(config, response)

            if refreshed_config is not None:
                return refreshed_config

        return None
