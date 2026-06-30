from dataclasses import dataclass
from typing import Any

from falcon.annotations.base import MISSING, Param


@dataclass(slots=True)
class HeaderParam(Param):
    convert_underscores: bool = True


def Header(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
    convert_underscores: bool = True,
) -> HeaderParam:
    if required is None:
        required = default is MISSING

    return HeaderParam(
        default=default,
        alias=alias,
        required=required,
        convert_underscores=convert_underscores,
    )
