import json
from asyncio import to_thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from falcon.core.types import RequestConfig, SimpleResponse
from falcon.runtime.base import ClientRuntime


class UrllibRuntime(ClientRuntime):
    async def request(self, config: RequestConfig) -> SimpleResponse:
        return await to_thread(self._request_sync, config)

    def _request_sync(self, config: RequestConfig) -> SimpleResponse:
        url = config.url

        if config.params:
            separator = "&" if "?" in url else "?"
            url = url + separator + urlencode(config.params, doseq=True)

        headers = dict(config.headers or {})
        body = None

        if config.json is not None:
            body = json.dumps(config.json).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        req = Request(
            url=url,
            data=body,
            headers=headers,
            method=config.method,
        )

        with urlopen(req) as response:
            content = response.read()

            json_data = None

            if content:
                try:
                    json_data = json.loads(content.decode("utf-8"))
                except Exception:
                    json_data = None

            return SimpleResponse(
                status_code=response.status,
                headers=dict(response.headers),
                content=content,
                json_data=json_data,
            )
