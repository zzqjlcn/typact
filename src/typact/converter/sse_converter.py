import codecs
import json
from collections.abc import AsyncIterator
from typing import Any

from pydantic import TypeAdapter


class SseResponseConverter:
    def convert(self, chunks: AsyncIterator[bytes], item_type: Any) -> AsyncIterator[Any]:
        async def iterator():
            decoder = codecs.getincrementaldecoder("utf-8")()
            buffer = ""
            data_lines: list[str] = []

            async for chunk in chunks:
                buffer += decoder.decode(chunk)
                lines = buffer.splitlines(keepends=True)
                buffer = ""

                if lines and not lines[-1].endswith(("\n", "\r")):
                    buffer = lines.pop()

                for line in lines:
                    item = line.rstrip("\r\n")
                    if not item:
                        if data_lines:
                            yield self._convert_data("\n".join(data_lines), item_type)
                            data_lines = []
                        continue
                    if item.startswith("data:"):
                        data_lines.append(item[5:].lstrip(" "))

            buffer += decoder.decode(b"", final=True)
            if buffer.startswith("data:"):
                data_lines.append(buffer[5:].lstrip(" "))
            if data_lines:
                yield self._convert_data("\n".join(data_lines), item_type)

        return iterator()

    @staticmethod
    def _convert_data(data: str, item_type: Any) -> Any:
        if item_type is str:
            return data

        try:
            value = json.loads(data)
        except json.JSONDecodeError:
            if item_type is Any:
                return data
            raise

        if item_type is Any:
            return value
        return TypeAdapter(item_type).validate_python(value)
