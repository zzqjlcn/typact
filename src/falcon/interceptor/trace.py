from falcon.core.types import RequestConfig


class TraceIdInterceptor:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    async def before_request(self, config: RequestConfig) -> RequestConfig:
        config.headers["X-Trace-Id"] = self.trace_id
        return config
