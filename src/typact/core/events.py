from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Literal

from typact.core.types import RequestConfig, Response

RequestEventPhase = Literal["request", "retry", "response", "failure"]


@dataclass(frozen=True)
class RequestEvent:
    phase: RequestEventPhase
    config: RequestConfig
    attempt: int
    response: Response | None = None
    error: Exception | None = None


RequestEventHandler = Callable[[RequestEvent], None | Awaitable[None]]
