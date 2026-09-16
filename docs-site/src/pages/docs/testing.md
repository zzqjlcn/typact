---
layout: ../../layouts/DocsLayout.astro
title: Testing
description: Verify request building with the Mock Runtime and no live server.
---

# Testing

The Mock Runtime lets tests focus on whether a declaration produced the correct request, without a network or live backend.

## Why use the Mock Runtime?

Typical HTTP mocks intercept the network layer. Typact's Mock Runtime replaces the transport boundary itself, making tests fast and deterministic while exposing the resulting request configuration.

## Basic test

```python
from typact import HttpClient, MockRuntime, Query


runtime = MockRuntime()
runtime.add_response(
    "GET",
    "https://api.example.com/items",
    json_data={"items": []},
)
client = HttpClient("https://api.example.com", client_runtime=runtime)


@client.get("/items")
async def list_items(page: int = Query(1)) -> dict:
    pass


result = await list_items(page=2)
assert result == {"items": []}
assert runtime.requests[0].params == {"page": 2}
```

## Streams and SSE

The Mock Runtime also provides deterministic chunks for streaming routes:

```python
runtime.add_stream_response(
    "GET",
    "https://api.example.com/download",
    [b"first", b"-second"],
)

runtime.add_sse_response(
    "GET",
    "https://api.example.com/events",
    ['data: {"value": 1}\n\n'],
)
```

Use `add_stream_response()` for raw streams and `add_sse_response()` for Server-Sent Events. Assert the converted events or chunks instead of depending on real network timing.

## Useful boundaries to test

Test URL and parameter construction, authentication and tracing interceptors, response type conversion, and error-prone edges such as multipart uploads.
