from abc import ABC, abstractmethod

from typact.core.types import RequestConfig, SimpleResponse


class ClientRuntime(ABC):
    @abstractmethod
    async def request(self, config: RequestConfig) -> SimpleResponse:
        raise NotImplementedError

    async def close(self) -> None:
        pass
