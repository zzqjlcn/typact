import inspect
from collections.abc import Callable
from dataclasses import dataclass, field

from typact.core.types import Response


_DEFAULT_RETRY_STATUS_CODES = frozenset({429, 502, 503, 504})


def default_should_retry_response(response: Response) -> bool:
    """Return whether the response has a default retryable HTTP status."""
    return response.status_code in _DEFAULT_RETRY_STATUS_CODES


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int = 0
    initial_delay: float = 0.5
    max_delay: float = 30.0
    retry_status_codes: frozenset[int] | None = None
    allowed_methods: frozenset[str] = field(
        default_factory=lambda: frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
    )
    should_retry_response: Callable[[Response], bool] | None = None

    def __post_init__(self):
        if self.should_retry_response is not None:
            if self.retry_status_codes is not None:
                raise ValueError("retry_status_codes and should_retry_response are mutually exclusive")
            if not callable(self.should_retry_response):
                raise TypeError("should_retry_response must be a synchronous callable returning bool")
            if inspect.iscoroutinefunction(self.should_retry_response) or inspect.iscoroutinefunction(
                getattr(self.should_retry_response, "__call__", None)
            ):
                raise TypeError("should_retry_response must be synchronous")
        elif self.retry_status_codes is None:
            object.__setattr__(self, "retry_status_codes", _DEFAULT_RETRY_STATUS_CODES)
        if self.max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0")
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be greater than or equal to 0")
        if self.max_delay < 0:
            raise ValueError("max_delay must be greater than or equal to 0")

    def allows_method(self, method: str) -> bool:
        return method.upper() in self.allowed_methods

    def matches_response(self, response: Response) -> bool:
        """Evaluate the response rule without applying attempt or method limits."""
        if self.should_retry_response is None:
            return response.status_code in (self.retry_status_codes or ())
        result = self.should_retry_response(response)
        if not isinstance(result, bool):
            if inspect.iscoroutine(result):
                result.close()
            raise TypeError("should_retry_response must return bool synchronously")
        return result

    def delay_for_retry(self, retry_number: int) -> float:
        return min(self.initial_delay * (2 ** retry_number), self.max_delay)
