from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from typact.core.types import RequestConfig, Response


class ClientRuntime(ABC):
    @abstractmethod
    async def request(self, config: RequestConfig) -> Response:
        raise NotImplementedError

    async def close(self) -> None:
        pass

    def stream(self, config: RequestConfig) -> AsyncIterator[bytes]:
        raise NotImplementedError("This runtime does not support streaming responses")
