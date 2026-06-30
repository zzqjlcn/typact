from falcon.core.types import RequestConfig


class BearerTokenInterceptor:
    def __init__(self, token: str):
        self.token = token

    async def before_request(self, config: RequestConfig) -> RequestConfig:
        config.headers["Authorization"] = f"Bearer {self.token}"
        return config


class ApiKeyInterceptor:
    def __init__(
        self,
        api_key: str,
        header_name: str = "X-API-Key",
    ):
        self.api_key = api_key
        self.header_name = header_name

    async def before_request(self, config: RequestConfig) -> RequestConfig:
        config.headers[self.header_name] = self.api_key
        return config
