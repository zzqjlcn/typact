from typing import Any

from pydantic import TypeAdapter

from typact.core.types import Response


class TypactHttpError(Exception):
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self.content = content
        super().__init__(f"Typact request failed: status_code={status_code}, body={content[:500]!r}")


class ResponseConverter:
    def convert(
        self,
        response: Response,
        return_type: Any,
    ):
        if return_type is Response:
            return response

        if response.status_code >= 400:
            raise TypactHttpError(response.status_code, response.content.decode())

        if return_type is None or return_type is type(None):
            return None

        if return_type is bytes:
            return response.content

        if not response.content:
            return None

        data = response.json()

        if return_type is Any:
            return data

        return TypeAdapter(return_type).validate_python(data)
