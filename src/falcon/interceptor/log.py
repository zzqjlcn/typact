from falcon.core.types import RequestConfig, SimpleResponse


class LoggingInterceptor:
    async def before_request(self, config: RequestConfig) -> RequestConfig:
        print(f"[Falcon] -> {config.method} {config.url}")
        return config

    async def after_response(self, response: SimpleResponse) -> SimpleResponse:
        print(f"[Falcon] <- {response.status_code}")
        return response
