import json
from asyncio import to_thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from typact.core.types import RequestConfig, Response
from typact.runtime.base import ClientRuntime


class UrllibRuntime(ClientRuntime):
    async def request(self, config: RequestConfig) -> Response:
        return await to_thread(self._request_sync, config)

    def _request_sync(self, config: RequestConfig) -> Response:
        url = config.url

        if config.params:
            separator = "&" if "?" in url else "?"
            url = url + separator + urlencode(config.params, doseq=True)

        headers = dict(config.headers or {})
        body = None

        if config.json is not None:
            body = json.dumps(config.json).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif config.data is not None:
            if isinstance(config.data, dict):
                body = urlencode(config.data, doseq=True).encode("utf-8")
                headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
            elif isinstance(config.data, str):
                body = config.data.encode("utf-8")
            else:
                body = config.data

        req = Request(
            url=url,
            data=body,
            headers=headers,
            method=config.method,
        )

        try:
            response = urlopen(req, timeout=config.timeout)
        except HTTPError as error:
            response = error

        with response:
            content = response.read()

            json_data = None

            if content:
                try:
                    json_data = json.loads(content.decode("utf-8"))
                except Exception:
                    json_data = None

            return Response(
                status_code=response.status if hasattr(response, "status") else response.code,
                headers=dict(response.headers),
                content=content,
                json_data=json_data,
            )
