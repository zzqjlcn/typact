from dataclasses import dataclass
from typing import Any

from falcon.annotations.base import MISSING, Param


@dataclass(slots=True)
class PathParam(Param):
    default: Any = MISSING
    required: bool = True


def Path(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool = True,
) -> PathParam:
    return PathParam(
        default=default,
        alias=alias,
        required=required,
    )
