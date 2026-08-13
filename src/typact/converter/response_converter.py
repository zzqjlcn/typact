from typing import Any

from pydantic import TypeAdapter

from typact.core.errors import TypactHttpError
from typact.core.types import Response


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
