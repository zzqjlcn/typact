from dataclasses import dataclass
from typing import Any

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class FormParam(Param):
    pass


def Form(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
) -> FormParam:
    if required is None:
        required = default is MISSING

    return FormParam(
        default=default,
        alias=alias,
        required=required,
    )
