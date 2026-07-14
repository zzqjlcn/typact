from dataclasses import dataclass
from typing import Any

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class PathParam(Param):
    default: Any = MISSING
    required: bool = True
    allow_slashes: bool = False


def Path(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool = True,
    allow_slashes: bool = False,
) -> PathParam:
    return PathParam(
        default=default,
        alias=alias,
        required=required,
        allow_slashes=allow_slashes,
    )
