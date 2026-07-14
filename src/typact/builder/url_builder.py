from dataclasses import dataclass
from urllib.parse import quote, urljoin


@dataclass(frozen=True)
class PathValue:
    value: object
    allow_slashes: bool = False


class UrlBuilder:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/") + "/"

    def build(
        self,
        path: str,
        path_params: dict[str, object],
    ) -> str:
        for key, value in path_params.items():
            safe = ""

            if isinstance(value, PathValue):
                safe = "/" if value.allow_slashes else ""
                value = value.value

            path = path.replace(
                "{" + key + "}",
                quote(str(value), safe=safe),
            )

        return urljoin(self.base_url, path.lstrip("/"))
