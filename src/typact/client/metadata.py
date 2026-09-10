import inspect
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RouteDefinition:
    method: str
    path: str
    signature: inspect.Signature
    return_type: Any
    is_async: bool
