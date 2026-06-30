from urllib.parse import quote, urljoin


class UrlBuilder:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/") + "/"

    def build(
        self,
        path: str,
        path_params: dict[str, object],
    ) -> str:
        for key, value in path_params.items():
            path = path.replace(
                "{" + key + "}",
                quote(str(value), safe=""),
            )

        return urljoin(self.base_url, path.lstrip("/"))
