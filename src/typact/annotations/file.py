from dataclasses import dataclass
from typing import Any, BinaryIO

from typact.annotations.base import MISSING, Param


@dataclass(slots=True)
class FileParam(Param):
    pass


@dataclass(slots=True)
class FileData:
    content: bytes | BinaryIO
    filename: str | None = None
    content_type: str | None = None


def File(
    default: Any = MISSING,
    *,
    alias: str | None = None,
    required: bool | None = None,
) -> FileParam:
    if required is None:
        required = default is MISSING

    return FileParam(
        default=default,
        alias=alias,
        required=required,
    )
