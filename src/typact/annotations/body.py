from dataclasses import dataclass
from typing import Any

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class BodyParam(Param):
    embed: bool = False


def Body(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
    embed: bool = False,
) -> BodyParam:
    if required is None:
        required = default is MISSING

    return BodyParam(
        default=default,
        alias=alias,
        required=required,
        embed=embed,
    )
