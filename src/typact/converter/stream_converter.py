import codecs
from collections.abc import AsyncIterator
from typing import Any


class StreamResponseConverter:
    def convert(self, chunks: AsyncIterator[bytes], item_type: Any) -> AsyncIterator[bytes | str]:
        if item_type is bytes:
            return self._bytes(chunks)
        if item_type is str:
            return self._text(chunks)
        raise TypeError("Stream responses must use AsyncIterator[bytes] or AsyncIterator[str]")

    @staticmethod
    async def _bytes(chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        async for chunk in chunks:
            yield chunk

    @staticmethod
    async def _text(chunks: AsyncIterator[bytes]) -> AsyncIterator[str]:
        decoder = codecs.getincrementaldecoder("utf-8")()

        async for chunk in chunks:
            text = decoder.decode(chunk)
            if text:
                yield text

        text = decoder.decode(b"", final=True)
        if text:
            yield text
