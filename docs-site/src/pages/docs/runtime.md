---
layout: ../../layouts/DocsLayout.astro
title: Runtimes and request policies
description: Choose urllib, httpx, or aiohttp and configure retries, streaming, and request events.
---

# Runtimes and request policies

The Runtime is Typact's only boundary with the network. Business contracts do not need to know which HTTP library sends the request.

## Standard-library Runtime

The default `UrllibRuntime` adds no HTTP dependency to the core installation:

```python
client = HttpClient("https://api.example.com")
```

## httpx

```python
import httpx
from typact import HttpClient, HttpxRuntime


client = HttpClient(
    "https://api.example.com",
    client_runtime=HttpxRuntime(httpx.AsyncClient(timeout=30)),
)
```

## aiohttp

```python
from typact import AioHttpRuntime, HttpClient


client = HttpClient(
    "https://api.example.com",
    client_runtime=AioHttpRuntime(),
)
```

Endpoint declarations and return types stay unchanged across Runtimes.

## Timeouts and retries

Configure default timeout and retry policies on `HttpClient`. Retries are disabled by default. When enabled, the default policy retries idempotent methods after network or timeout errors and after `429`, `502`, `503`, or `504` responses.

```python
from typact import HttpClient, RetryConfig


client = HttpClient(
    "https://api.example.com",
    timeout=10,
    retry_config=RetryConfig(max_retries=3, initial_delay=0.5),
)
```

Connection failures raise `TypactNetworkError`; timeouts raise `TypactTimeoutError`.

An endpoint can override the client policy. An explicit `None` disables the inherited value:

```python
from collections.abc import AsyncIterator

from typact import Path, RetryConfig


@client.get(
    "/reports/{report_id}",
    timeout=60,
    retry_config=RetryConfig(max_retries=2),
)
async def get_report(report_id: int = Path()) -> dict:
    pass


@client.get("/events", timeout=None)
async def events() -> AsyncIterator[dict]:
    pass
```

## Retry based on response content

Regular requests can use a synchronous `should_retry_response: Callable[[Response], bool]` callback. The callback always receives Typact's unified `Response`, with `status_code`, `headers`, `content`, `text`, and `json()` available.

```python
from typact import HttpClient, Response, RetryConfig, default_should_retry_response


def retry_response(response: Response) -> bool:
    if default_should_retry_response(response):
        return True
    data = response.json()
    return (
        response.status_code == 200
        and isinstance(data, dict)
        and data.get("code") in {"SYSTEM_BUSY", "RATE_LIMITED"}
    )


client = HttpClient(
    "https://api.example.com",
    retry_config=RetryConfig(
        max_retries=3,
        should_retry_response=retry_response,
    ),
)
```

The following rules keep retry behavior explicit:

- Without a callback, `retry_status_codes` controls response retries and defaults to `{429, 502, 503, 504}`.
- With a callback, that callback fully controls response retries. Call `default_should_retry_response()` when you also want the default status-code behavior.
- Providing both a non-`None` `retry_status_codes` value and a callback raises `ValueError`.
- `max_retries`, `allowed_methods`, and backoff settings always apply. POST is excluded from the default method set.
- Returning `False` stops response retry evaluation but does not disable network-error retries. Use `max_retries=0` or a route-level `retry_config=None` to disable all retries.
- The callback must synchronously return `bool`. Its exceptions propagate and emit a `failure` event.
- Evaluation happens before response interceptors, the `response` event, and return-type conversion.
- After retries are exhausted, the last response continues through the normal response pipeline.
- Authentication refresh for a `401` happens after the response retry loop. A response callback should normally return `False` for `401`.

Streaming and SSE routes do not expose a complete `Response`, so they cannot use a response callback. Give those routes a status-code policy or disable inherited retries:

```python
from collections.abc import AsyncIterator


@client.get("/events", retry_config=RetryConfig(max_retries=2))
async def events() -> AsyncIterator[dict]:
    pass
```

## Streaming responses

`HttpxRuntime` and `AioHttpRuntime` support raw streams and Server-Sent Events. `UrllibRuntime` supports complete responses only.

```python
from collections.abc import AsyncIterator


@client.get("/files/report.zip")
async def download_report() -> AsyncIterator[bytes]:
    pass


async for chunk in download_report():
    await write_chunk(chunk)
```

`AsyncIterator[str]` applies incremental UTF-8 decoding. Other `AsyncIterator[T]` declarations parse each SSE `data:` payload and convert it into `T`.

Streaming retries stop before the first chunk is delivered, preventing already-consumed data from being delivered twice.

## Request lifecycle events

Pass `event_handlers` to `HttpClient` to observe `request`, `retry`, `response`, and `failure` phases. Handlers can be synchronous or asynchronous and are suitable for logs, metrics, and traces.

```python
from typact import HttpClient, RequestEvent


async def observe(event: RequestEvent):
    print(event.phase, event.config.method, event.config.url, event.attempt)


client = HttpClient(
    "https://api.example.com",
    event_handlers=[observe],
)
```

Call `client.add_event_handler(handler)` to register another handler later. A regular `response` event includes the Typact `Response`. For streams, it fires when the connection succeeds and carries `response=None`. A final failure includes the exception.
