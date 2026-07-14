from dataclasses import dataclass
from typing import Any


MISSING = object()


@dataclass(slots=True)
class Param:
    default: Any = MISSING
    alias: str | None = None
    required: bool = True
