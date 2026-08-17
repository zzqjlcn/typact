---
layout: ../../layouts/DocsLayout.astro
title: Runtime
description: 在 urllib、httpx 与 aiohttp Runtime 之间选择。
---

# Runtime

Runtime 是 Typact 与网络之间唯一的边界。业务契约不需要知道底层使用哪个 HTTP 库。

## 标准库 Runtime

默认配置使用 `UrllibRuntime`，核心安装不引入额外 HTTP 依赖：

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

无论选择哪个 Runtime，接口声明和返回类型都保持不变。

## 超时与重试

在 `HttpClient` 上配置默认超时与重试策略。默认不自动重试；启用后仅重试幂等方法的网络/超时错误，以及 429、502、503、504 响应，避免意外重复创建数据。

```python
from typact import HttpClient, RetryConfig

client = HttpClient(
    "https://api.example.com",
    timeout=10,
    retry_config=RetryConfig(max_retries=3, initial_delay=0.5),
)
```

网络连接失败会抛出 `TypactNetworkError`，超时会抛出 `TypactTimeoutError`。

## 流式响应

`HttpxRuntime` 和 `AioHttpRuntime` 支持普通流与 SSE；默认的 `UrllibRuntime` 仅支持一次性响应。

```python
from collections.abc import AsyncIterator

@client.get("/files/report.zip")
async def download_report() -> AsyncIterator[bytes]:
    pass

async for chunk in download_report():
    await write_chunk(chunk)
```

将返回类型声明为 `AsyncIterator[str]` 时，Typact 会进行 UTF-8 增量解码；声明为其他 `AsyncIterator[T]` 时，会按 SSE 的 `data:` 事件解析并转换为 `T`。
