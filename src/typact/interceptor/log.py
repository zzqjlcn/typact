from typact.core.types import RequestConfig, SimpleResponse


class LoggingInterceptor:
    async def before_request(self, config: RequestConfig) -> RequestConfig:
        print(f"[Typact] -> {config.method} {config.url}")
        return config

    async def after_response(self, response: SimpleResponse) -> SimpleResponse:
        print(f"[Typact] <- {response.status_code}")
        return response
