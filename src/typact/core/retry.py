from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int = 0
    initial_delay: float = 0.5
    max_delay: float = 30.0
    retry_status_codes: frozenset[int] = field(
        default_factory=lambda: frozenset({429, 502, 503, 504})
    )
    allowed_methods: frozenset[str] = field(
        default_factory=lambda: frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
    )

    def __post_init__(self):
        if self.max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0")
        if self.initial_delay < 0:
            raise ValueError("initial_delay must be greater than or equal to 0")
        if self.max_delay < 0:
            raise ValueError("max_delay must be greater than or equal to 0")

    def allows_method(self, method: str) -> bool:
        return method.upper() in self.allowed_methods

    def delay_for_retry(self, retry_number: int) -> float:
        return min(self.initial_delay * (2 ** retry_number), self.max_delay)
