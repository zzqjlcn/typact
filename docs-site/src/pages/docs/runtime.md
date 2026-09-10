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

单个接口可以覆盖 Client 默认策略；`None` 表示关闭继承的默认值：

```python
from collections.abc import AsyncIterator

from typact import Path, RetryConfig

@client.get("/reports/{report_id}", timeout=60, retry_config=RetryConfig(max_retries=2))
async def get_report(report_id: int = Path()) -> dict:
    pass

@client.get("/events", timeout=None)
async def events() -> AsyncIterator[dict]:
    pass
```

## 根据响应内容重试

普通请求可通过同步回调 `should_retry_response: Callable[[Response], bool]` 判断是否重试。参数始终是统一的 `typact.Response`，可读取 `status_code`、`headers`、`content`、`text` 和 `json()`，不是接口声明的返回模型或底层 HTTP 库的响应对象。

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

配置规则：

- 不提供回调时，`retry_status_codes` 继续控制状态码重试，默认值为 `{429, 502, 503, 504}`，旧配置无需修改。
- 提供回调时，完全由它决定普通响应是否需要重试。默认状态码不会额外生效；需要时显式调用 `default_should_retry_response`。
- 同时提供非 `None` 的 `retry_status_codes` 和回调会抛出 `ValueError`，包括空集合和默认集合。`retry_status_codes=None` 表示未指定；无回调时会解析为默认集合，有回调时保持 `None`。
- `max_retries`、`allowed_methods` 和退避配置始终生效。默认 `max_retries=0` 不开启重试；默认方法集合不含 POST，确认接口允许重复请求后才应将它加入。
- 回调返回 `False` 只结束响应重试判断，不关闭网络异常重试。禁用全部重试使用 `max_retries=0` 或路由级 `retry_config=None`。
- 回调仅在方法允许且尚有重试次数时调用；必须同步返回 `bool`。异步函数和非布尔返回值不受支持，回调抛出的异常直接传播并触发 `failure`，不会作为网络错误重试。
- 判断发生在响应拦截器、`response` 事件和返回类型转换之前。触发重试时，`retry` 事件携带本次响应。
- 重试耗尽后，最后一次响应进入原有处理流程。HTTP 200 的业务错误不会自动转换为新的业务异常。
- 原有 401 认证刷新发生在响应重试循环结束后。若回调对 401 返回 `True`，会先用完该循环的重试机会，再进入认证刷新；通常应让 401 返回 `False`。认证刷新后的请求同样使用该策略。

流式请求与 SSE 目前不提供完整的 `Response`，不支持这个回调；使用回调配置调用它们会在网络请求前抛出 `ValueError`，不会静默忽略策略。混合使用普通和流式接口时，为流式路由指定状态码策略或关闭重试：

```python
from collections.abc import AsyncIterator


@client.get("/events", retry_config=RetryConfig(max_retries=2))
async def events() -> AsyncIterator[dict]:
    pass
```

流式状态码和网络异常重试仍只发生在第一个数据块交付之前。

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
流式连接只会在首个分片产出前重试，避免重复交付已消费的数据。

## 请求事件

`HttpClient` 可通过 `event_handlers` 观察请求生命周期，事件阶段为 `request`、`retry`、`response` 和 `failure`。处理函数可以是同步或异步函数，适合接入日志、指标与链路追踪。

```python
from typact import HttpClient, RequestEvent

async def observe(event: RequestEvent):
    print(event.phase, event.config.method, event.config.url, event.attempt)

client = HttpClient("https://api.example.com", event_handlers=[observe])
```

也可以在创建后追加处理器：`client.add_event_handler(handler)`。`response` 事件会提供普通请求的 `Response`；流式请求在连接建立成功时触发，响应字段为 `None`。`failure` 会提供最终异常。
