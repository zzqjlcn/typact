import inspect
from dataclasses import dataclass
from typing import Any

from typact.core.retry import RetryConfig


UNSET = object()


@dataclass(frozen=True)
class RouteDefinition:
    method: str
    path: str
    signature: inspect.Signature
    return_type: Any
    is_async: bool
    timeout: float | None | object = UNSET
    retry_config: RetryConfig | None | object = UNSET
