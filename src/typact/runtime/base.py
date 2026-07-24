from abc import ABC, abstractmethod

from typact.core.types import RequestConfig, Response


class ClientRuntime(ABC):
    @abstractmethod
    async def request(self, config: RequestConfig) -> Response:
        raise NotImplementedError

    async def close(self) -> None:
        pass
