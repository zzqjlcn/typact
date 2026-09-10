from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestConfig:
    method: str
    url: str
    params: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, Any] = field(default_factory=dict)
    cookies: dict[str, Any] = field(default_factory=dict)
    json: Any = None
    data: Any = None
    files: Any = None
    timeout: float | None = None


@dataclass
class Response:
    status_code: int
    headers: dict[str, str]
    content: bytes
    json_data: Any = None

    def json(self) -> Any:
        return self.json_data

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")


SimpleResponse = Response
