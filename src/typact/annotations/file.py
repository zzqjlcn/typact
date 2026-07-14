from dataclasses import dataclass
from typing import Any

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class FileParam(Param):
    filename: str | None = None
    content_type: str | None = None


def File(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
    filename: str | None = None,
    content_type: str | None = None,
) -> FileParam:
    if required is None:
        required = default is MISSING

    return FileParam(
        default=default,
        alias=alias,
        required=required,
        filename=filename,
        content_type=content_type,
    )
