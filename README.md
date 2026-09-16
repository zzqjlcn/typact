# <img src="https://typact.zzq.jl.cn/favicon.svg" alt="Typact" width="28" height="28" style="vertical-align: middle;"/> Typact

[![Documentation](https://img.shields.io/badge/docs-typact.zzq.jl.cn-blue)](https://typact.zzq.jl.cn)
[![PyPI](https://img.shields.io/pypi/v/typact)](https://pypi.org/project/typact/)
[![Python](https://img.shields.io/pypi/pyversions/typact)](https://pypi.org/project/typact/)
[![CI](https://github.com/zzqjlcn/typact/actions/workflows/ci.yml/badge.svg)](https://github.com/zzqjlcn/typact/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/typact)](https://github.com/zzqjlcn/typact/blob/main/LICENSE)

[Documentation](https://typact.zzq.jl.cn) · [PyPI](https://pypi.org/project/typact/) · [中文 README](https://github.com/zzqjlcn/typact/blob/main/README.zh-CN.md) · [Changelog](https://github.com/zzqjlcn/typact/blob/main/CHANGELOG.md)

**Build production-ready Python API clients with FastAPI-style declarations.**

Typact turns an annotated Python function into an executable HTTP contract. Declare the request parameters and return type once; Typact handles request building, transport, response validation, retries, authentication, streaming, and test doubles.

```python
from pydantic import BaseModel

from typact import HttpClient, Path


class User(BaseModel):
    id: int
    name: str


client = HttpClient("https://api.example.com")


@client.get("/users/{user_id}")
async def get_user(user_id: int = Path()) -> User:
    pass


user = await get_user(1)
```

## Why Typact?

Handwritten clients tend to repeat the same plumbing: assemble URLs and headers, serialize bodies, check status codes, validate JSON, retry transient failures, refresh tokens, and mock the network in tests. Typact keeps that behavior behind one typed contract.

- **FastAPI-style declarations** with `Path`, `Query`, `Header`, `Cookie`, `Body`, `Form`, and `File`.
- **Validated return types** powered by Pydantic v2 `TypeAdapter`.
- **Production request policies** including timeouts, exponential backoff, response-aware retries, and token refresh.
- **Streaming support** for raw byte/text streams and typed Server-Sent Events.
- **Pluggable transports** using the standard library, httpx, aiohttp, or a custom Runtime.
- **Deterministic tests** through a Mock Runtime that records the request Typact built.
- **Small core install** with Pydantic as the only required dependency.

Typact is async-first and targets Python 3.10 through 3.14.

## Installation

The default Runtime uses Python's standard library:

```bash
pip install typact
```

Install an optional transport when you need httpx or aiohttp:

```bash
pip install "typact[httpx]"
pip install "typact[aiohttp]"
```

## Quick start

```python
import asyncio

from pydantic import BaseModel, ConfigDict, Field

from typact import Body, HttpClient, Path, Query


class Todo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    id: int | None = None
    title: str
    completed: bool


client = HttpClient("https://jsonplaceholder.typicode.com")


@client.get("/todos/{todo_id}")
async def get_todo(todo_id: int = Path()) -> Todo:
    pass


@client.get("/todos")
async def list_todos(user_id: int = Query(alias="userId")) -> list[Todo]:
    pass


@client.post("/todos")
async def create_todo(todo: Todo = Body()) -> Todo:
    pass


async def main():
    todo = await get_todo(1)
    todos = await list_todos(user_id=1)
    created = await create_todo(
        Todo(user_id=1, title="Try Typact", completed=False)
    )
    print(todo, todos[0], created)
    await client.close()


asyncio.run(main())
```

## Production request policies

Configure shared timeout and retry behavior on the client, then override it per route when an endpoint needs different semantics:

```python
from typact import HttpClient, Path, RetryConfig


client = HttpClient(
    "https://api.example.com",
    timeout=10,
    retry_config=RetryConfig(max_retries=3, initial_delay=0.5),
)


@client.get(
    "/reports/{report_id}",
    timeout=60,
    retry_config=RetryConfig(max_retries=2),
)
async def get_report(report_id: int = Path()) -> dict:
    pass
```

Retries are disabled by default. When enabled, the default policy retries network and timeout failures plus `429`, `502`, `503`, and `504` responses for idempotent methods.

Typact can also retry a successful HTTP response that carries a transient business error:

```python
from typact import Response, RetryConfig, default_should_retry_response


def should_retry(response: Response) -> bool:
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
        should_retry_response=should_retry,
    ),
)
```

See the [Runtime guide](https://typact.zzq.jl.cn/docs/runtime/) for inheritance rules, streaming behavior, and lifecycle events.

## Authentication and cross-cutting behavior

Interceptors keep authentication, logging, and tracing out of endpoint declarations:

```python
from typact import BearerTokenInterceptor, HttpClient, InterceptorChain


client = HttpClient(
    "https://api.example.com",
    interceptor_chain=InterceptorChain(
        request_interceptors=[BearerTokenInterceptor("your-token")],
    ),
)
```

Built-in interceptors include bearer tokens, refreshable bearer tokens, API keys, trace IDs, and logging.

## Files and streaming

Upload multipart files with `FileData`:

```python
from typact import File, FileData


@client.post("/upload")
async def upload(file: FileData = File()) -> dict:
    pass


await upload(
    FileData(
        content=b"hello",
        filename="hello.txt",
        content_type="text/plain",
    )
)
```

Use `AsyncIterator[bytes]` or `AsyncIterator[str]` for raw streams. Other item types are decoded from Server-Sent Events:

```python
from collections.abc import AsyncIterator


@client.get("/events")
async def events() -> AsyncIterator[dict]:
    pass


async for event in events():
    print(event)
```

Streaming requires the httpx or aiohttp Runtime. Retries stop after the first chunk has been delivered, preventing duplicate data.

## Pluggable Runtimes

The default `UrllibRuntime` needs no extra HTTP dependency. Existing httpx and aiohttp clients can be injected when you need their connection settings or ecosystem integrations:

```python
import httpx

from typact import HttpClient, HttpxRuntime


client = HttpClient(
    "https://api.example.com",
    client_runtime=HttpxRuntime(httpx.AsyncClient(timeout=30)),
)
```

Endpoint declarations and return types stay unchanged when the Runtime changes.

## Testing without a server

The Mock Runtime replaces the transport boundary and records every built request:

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

## Documentation and examples

- [Getting started](https://typact.zzq.jl.cn/docs/getting-started/)
- [Parameter annotations](https://typact.zzq.jl.cn/docs/annotations/)
- [Runtimes, retries, streaming, and events](https://typact.zzq.jl.cn/docs/runtime/)
- [Interceptors](https://typact.zzq.jl.cn/docs/interceptors/)
- [Testing](https://typact.zzq.jl.cn/docs/testing/)
- [`examples/`](https://github.com/zzqjlcn/typact/tree/main/examples)

## Development

```bash
uv sync --all-extras --group dev
uv run --no-sync pytest -q
```

Design changes must account for public API clarity, Runtime consistency, backward compatibility, and migration cost. See [CONTRIBUTING.md](https://github.com/zzqjlcn/typact/blob/main/CONTRIBUTING.md) and [RELEASING.md](https://github.com/zzqjlcn/typact/blob/main/RELEASING.md) before contributing or publishing.

## License

Typact is released under the [MIT License](https://github.com/zzqjlcn/typact/blob/main/LICENSE).
