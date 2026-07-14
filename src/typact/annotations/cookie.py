from dataclasses import dataclass
from typing import Any

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class CookieParam(Param):
    pass


def Cookie(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
) -> CookieParam:
    if required is None:
        required = default is MISSING

    return CookieParam(
        default=default,
        alias=alias,
        required=required,
    )
