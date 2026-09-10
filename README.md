# <img src="https://typact.zzq.jl.cn/favicon.svg" alt="Typact" width="28" height="28" style="vertical-align: middle;"/> Typact

[![Documentation](https://img.shields.io/badge/docs-typact.zzq.jl.cn-blue)](https://typact.zzq.jl.cn)
[![PyPI](https://img.shields.io/pypi/v/typact)](https://pypi.org/project/typact/)
[![Python](https://img.shields.io/pypi/pyversions/typact)](https://pypi.org/project/typact/)
[![License](https://img.shields.io/pypi/l/typact)](LICENSE)

**Typact** 是一个面向 Python 的声明式、类型安全、可插拔 Runtime 的 HTTP 服务调用框架。

它让你用类似 FastAPI 参数声明的方式定义远程 HTTP API，同时把请求构建、运行时传输、响应转换、认证、日志、Mock 测试拆成清晰的模块。

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

## 特性

- **声明式 HTTP Client**：用装饰器描述远程 API，而不是手写请求代码。
- **类型安全响应转换**：基于 Pydantic v2 `TypeAdapter` 将响应数据转换为模型、列表或任意类型。
- **FastAPI 风格参数注解**：支持 `Path`、`Query`、`Header`、`Cookie`、`Body`、`Form`、`File`。
- **多 Runtime**：默认使用标准库 `urllib`，也可按需安装 `httpx` 或 `aiohttp`。
- **拦截器链**：支持请求前和响应后的扩展点，可用于认证、日志、Trace 等。
- **Token 自动刷新**：支持 Token Provider 与 401 自动刷新重试。
- **超时与重试**：支持 Client / API 级别超时配置与指数退避重试。
- **Mock Runtime**：无需启动服务即可测试声明式 Client 的请求构建结果。
- **文件上传 / 下载**：支持 `multipart/form-data`、原始字节下载和流式下载。
- **SSE / Stream**：支持 `AsyncIterator[T]` 声明 SSE 和普通流式响应。

## 安装

Typact 要求：

```text
Python >= 3.13
```

核心安装只依赖 `pydantic`，默认 Runtime 使用 Python 标准库 `urllib`：

```bash
pip install typact
```

使用 `httpx` Runtime：

```bash
pip install "typact[httpx]"
```

使用 `aiohttp` Runtime：

```bash
pip install "typact[aiohttp]"
```

本地开发：

```bash
uv sync
```

## 快速开始

```python
import asyncio

from pydantic import BaseModel, ConfigDict, Field

from typact import Body, Header, HttpClient, Path, Query


class Todo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    id: int | None = None
    title: str
    completed: bool


client = HttpClient("https://jsonplaceholder.typicode.com")


@client.get("/todos/{todo_id}")
async def get_todo(
    todo_id: int = Path(),
    request_id: str = Header("req-001", alias="X-Request-Id"),
) -> Todo:
    pass


@client.get("/todos")
async def query_todos(
    user_id: int | None = Query(None, alias="userId"),
) -> list[Todo]:
    pass


@client.post("/todos")
async def create_todo(todo: Todo = Body()) -> Todo:
    pass


async def main():
    todo = await get_todo(1)
    print(todo)

    todos = await query_todos(user_id=1)
    print(todos[0])

    created = await create_todo(
        Todo(
            user_id=1,
            title="hello typact",
            completed=False,
        )
    )
    print(created)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

更多完整示例见 `examples/`：

- `examples/jsonplaceholder_demo.py`
- `examples/auth_demo.py`
- `examples/file_upload_demo.py`

完整使用文档请访问：

👉 **[Typact 官方文档](https://typact.zzq.jl.cn)**

## 参数注解

Typact 提供以下声明式参数：

```python
from typact import Body, Cookie, File, Form, Header, Path, Query
```

### Path

```python
@client.get("/users/{user_id}")
async def get_user(user_id: int = Path()) -> dict:
    pass
```

### Query

```python
@client.get("/users")
async def list_users(
    page: int = Query(1),
    keyword: str | None = Query(None),
) -> list[dict]:
    pass
```

### Header

```python
@client.get("/profile")
async def get_profile(
    request_id: str = Header(alias="X-Request-Id"),
) -> dict:
    pass
```

### Body

```python
@client.post("/users")
async def create_user(payload: dict = Body()) -> dict:
    pass
```

### Form

```python
@client.post("/auth/login")
async def login(
    name: str = Form(),
    password: str = Form(),
) -> dict:
    pass
```

### File

```python
from typact import File, FileData


@client.post("/upload")
async def upload_avatar(
    avatar: FileData = File(alias="file"),
) -> dict:
    pass


await upload_avatar(
    FileData(
        content=b"hello typact",
        filename="avatar.txt",
        content_type="text/plain",
    )
)
```

`File(...)` 负责声明文件字段名称、默认值和是否必填；`FileData(...)` 描述本次上传的内容、文件名和媒体类型。

只需要上传字节内容时，也可以直接使用：

```python
@client.post("/upload/raw")
async def upload_raw(file: bytes = File()) -> dict:
    pass


await upload_raw(b"hello typact")
```

## Runtime

Typact 的核心不会绑定某个 HTTP 库。

默认使用 `UrllibRuntime`，无需安装额外 HTTP Client 依赖：

```python
from typact import HttpClient


client = HttpClient("https://api.example.com")
```

### Httpx

```python
import httpx

from typact import HttpClient, HttpxRuntime


client = HttpClient(
    "https://api.example.com",
    client_runtime=HttpxRuntime(
        httpx.AsyncClient(timeout=30)
    ),
)
```

### Aiohttp

```python
from typact import AioHttpRuntime, HttpClient


client = HttpClient(
    "https://api.example.com",
    client_runtime=AioHttpRuntime(),
)
```

### Mock

```python
from typact import HttpClient, MockRuntime, Path


runtime = MockRuntime()

runtime.add_response(
    "GET",
    "http://test.local/users/1",
    json_data={
        "id": 1,
        "name": "typact",
    },
)

client = HttpClient(
    "http://test.local",
    client_runtime=runtime,
)


@client.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(),
) -> dict:
    pass
```

## 超时与重试

默认不会自动重试。

生产环境可以在 Client 上配置超时和指数退避：

```python
from typact import HttpClient, RetryConfig


client = HttpClient(
    "https://api.example.com",
    timeout=10,
    retry_config=RetryConfig(
        max_retries=3,
        initial_delay=0.5,
    ),
)
```

单个 API 也可以覆盖 Client 默认配置：

```python
@client.get(
    "/reports/{report_id}",
    timeout=60,
    retry_config=RetryConfig(max_retries=2),
)
async def get_report(
    report_id: int = Path(),
) -> dict:
    pass
```

## Response

所有 Runtime 都会映射成统一的 `typact.Response`：

```python
from typact import Response


@client.get("/health")
async def health() -> Response:
    pass


response = await health()

print(response.status_code)
print(response.headers)
print(response.content)
print(response.text)
print(response.json())
```

返回类型声明为 `Response` 时，Typact 不会为 `4xx / 5xx` 自动抛出 `TypactHttpError`，调用方可以自行根据 `status_code` 处理。

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

## 拦截器

拦截器可以在请求发送前或响应转换前处理数据：

```python
from typact import (
    ApiKeyInterceptor,
    BearerTokenInterceptor,
    HttpClient,
    InterceptorChain,
)


client = HttpClient(
    "https://api.example.com",
    interceptor_chain=InterceptorChain(
        request_interceptors=[
            BearerTokenInterceptor("token"),
            ApiKeyInterceptor("api-key"),
        ],
    ),
)
```

内置拦截器：

- `BearerTokenInterceptor`
- `RefreshableBearerTokenInterceptor`
- `ApiKeyInterceptor`
- `TraceIdInterceptor`
- `LoggingInterceptor`

## Token 刷新

对于会过期的 Token，可以使用 `CallableTokenProvider` 和 `RefreshableBearerTokenInterceptor`：

```python
from typact import (
    CallableTokenProvider,
    HttpClient,
    InterceptorChain,
    RefreshableBearerTokenInterceptor,
)


async def login() -> str:
    return "new-token"


token_provider = CallableTokenProvider(
    login,
    token="expired-token",
)

client = HttpClient(
    "https://api.example.com",
    interceptor_chain=InterceptorChain(
        request_interceptors=[
            RefreshableBearerTokenInterceptor(
                token_provider
            ),
        ],
    ),
)
```

当请求返回 `401` 时，Typact 会调用 `refresh_token()` 获取新 Token，并自动重试一次。

默认请求头：

```text
Authorization: Bearer <token>
```

如果接口要求：

```text
Authorization: <token>
```

可以使用：

```python
RefreshableBearerTokenInterceptor(
    token_provider,
    scheme=None,
)
```

## 文件上传

```python
from typact import File, FileData, HttpClient


client = HttpClient("https://api.example.com")


@client.post("/upload")
async def upload_file(
    file: FileData = File(),
) -> dict:
    pass


await upload_file(
    FileData(
        content=b"hello",
        filename="hello.txt",
        content_type="text/plain",
    )
)
```

## 文件下载

将返回类型声明为 `bytes`：

```python
@client.get("/files/report.pdf")
async def download_file() -> bytes:
    pass


content = await download_file()
```

Typact 会直接返回原始响应体，不经过 JSON 解析或 Pydantic 转换。

## SSE

将返回类型声明为 `AsyncIterator[T]`：

```python
from collections.abc import AsyncIterator

from typact import HttpClient


client = HttpClient("https://api.example.com")


@client.get("/events")
async def events() -> AsyncIterator[dict]:
    pass


async for event in events():
    print(event)
```

SSE 需要 `HttpxRuntime` 或 `AioHttpRuntime`。

## 普通流式响应

返回 `AsyncIterator[bytes]` 时会直接返回网络分片：

```python
from collections.abc import AsyncIterator


@client.get("/files/report.zip")
async def download_report() -> AsyncIterator[bytes]:
    pass


async for chunk in download_report():
    await write_chunk(chunk)
```

声明为 `AsyncIterator[str]` 时，会执行 UTF-8 增量解码。

## 项目结构

```text
src/typact/
├── annotations/      # Path / Query / Header / Cookie / Body / Form / File
├── builder/          # URL、请求、multipart 构建
├── client/           # HttpClient、路由装饰器、RouteDefinition
├── converter/        # 响应转换器
├── core/             # RequestConfig、Response
├── interceptor/      # 认证、日志、Trace、拦截器链
├── runtime/          # urllib、httpx、aiohttp、mock
└── testing/          # 测试辅助导出
```

## 设计理念

Typact 的核心流水线：

```text
Decorator
    ↓
RouteDefinition
    ↓
RequestBuilder
    ↓
InterceptorChain
    ↓
ClientRuntime
    ↓
ResponseConverter
```

每层只负责一件事：

- **Decorator**：收集函数签名和返回类型。
- **RequestBuilder**：将调用参数转换成 `RequestConfig`。
- **InterceptorChain**：处理认证、日志、Trace 等横切逻辑。
- **ClientRuntime**：负责实际 HTTP 请求。
- **ResponseConverter**：将响应转换成声明的目标类型。

## 开发

安装依赖：

```bash
uv sync
```

运行示例：

```bash
uv run python examples/jsonplaceholder_demo.py
uv run python examples/auth_demo.py
uv run python examples/file_upload_demo.py
```

编译检查：

```bash
uv run python -m compileall src examples
```

## 路线图

- 更完整的 multipart 文件上传能力
- Retry / Backoff
- OpenTelemetry
- OpenAPI 生成器
- SSE / Stream 响应转换
- Record / Replay 测试工具

## 文档

完整文档、API 使用说明及更多示例：

🌐 **[https://typact.zzq.jl.cn](https://typact.zzq.jl.cn)**

PyPI：

📦 **[https://pypi.org/project/typact/](https://pypi.org/project/typact/)**

## License

本项目基于 [MIT License](LICENSE) 开源。
