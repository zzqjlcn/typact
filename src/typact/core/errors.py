class TypactNetworkError(Exception):
    """A network failure prevented a request from completing."""

    def __init__(self, message: str, *, cause: Exception):
        self.cause = cause
        super().__init__(message)


class TypactTimeoutError(TypactNetworkError):
    """A request exceeded its configured timeout."""

    def __init__(self, timeout: float):
        self.timeout = timeout
        super().__init__(f"Typact request timed out after {timeout} seconds", cause=TimeoutError())
