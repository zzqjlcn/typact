class TypactHttpError(Exception):
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self.content = content
        super().__init__(f"Typact request failed: status_code={status_code}, body={content[:500]!r}")


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
