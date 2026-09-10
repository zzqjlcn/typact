from dataclasses import dataclass
from typing import Any

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class QueryParam(Param):
    pass


def Query(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
) -> QueryParam:
    if required is None:
        required = default is MISSING

    return QueryParam(
        default=default,
        alias=alias,
        required=required,
    )
