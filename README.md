# Typact

Typact 是一个面向 Python 的声明式、类型安全、可插拔 Runtime 的 HTTP 服务调用框架。

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

- 声明式 HTTP Client：用装饰器描述远程 API，而不是手写请求代码。
- 类型安全响应转换：基于 Pydantic v2 `TypeAdapter` 将响应数据转换为模型、列表或任意类型。
- FastAPI 风格参数注解：支持 `Path`、`Query`、`Header`、`Cookie`、`Body`、`Form`、`File`。
- 多 Runtime：默认使用标准库 `urllib`，也可按需安装 `httpx` 或 `aiohttp`。
- 拦截器链：支持请求前和响应后的扩展点，可用于认证、日志、Trace 等。
- Mock Runtime：无需启动服务即可测试声明式 client 的请求构建结果。
- 文件上传：支持通过 `File(...)` 构建 `multipart/form-data` 所需的 `files` 参数。

## 安装

核心安装只依赖 `pydantic`，默认 Runtime 使用 Python 标准库 `urllib`。

```bash
pip install typact
```

如果需要 `httpx` Runtime：

```bash
pip install "typact[httpx]"
```

如果需要 `aiohttp` Runtime：

```bash
pip install "typact[aiohttp]"
```

本仓库本地开发：

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
        Todo(user_id=1, title="hello typact", completed=False)
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

## 参数注解

Typact 当前提供以下声明式参数：

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
async def list_users(page: int = Query(1), keyword: str | None = Query(None)) -> list[dict]:
    pass
```

### Header

```python
@client.get("/profile")
async def get_profile(request_id: str = Header(alias="X-Request-Id")) -> dict:
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

`File(...)` 只声明文件字段的名称、默认值和是否必填；`FileData(...)`
描述本次上传的内容、文件名和媒体类型。构建请求时，它们会被转换为 Runtime
可直接消费的 `RequestConfig.files`。

只需要上传字节内容时，也可以直接使用 `bytes` 参数：

```python
@client.post("/upload/raw")
async def upload_raw(file: bytes = File()) -> dict:
    pass


await upload_raw(b"hello typact")
```

## Runtime

Typact 的核心不会绑定某个 HTTP 库。`HttpClient` 默认使用 `UrllibRuntime`，不需要安装额外依赖。

```python
from typact import HttpClient


client = HttpClient("https://api.example.com")
```

### 超时与重试

默认不会自动重试。生产调用可在 Client 上启用超时和指数退避；默认只重试幂等方法的连接/超时错误，以及 429、502、503、504 响应：

```python
from typact import HttpClient, RetryConfig

client = HttpClient(
    "https://api.example.com",
    timeout=10,
    retry_config=RetryConfig(max_retries=3, initial_delay=0.5),
)
```

所有 Runtime 都可以映射为统一的 `typact.Response`：

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

返回类型声明为 `Response` 时，Typact 不会为 4xx/5xx 自动抛出
`TypactHttpError`，由调用方根据 `response.status_code` 处理。

使用 `httpx`：

```python
import httpx

from typact import HttpClient, HttpxRuntime


client = HttpClient(
    "https://api.example.com",
    client_runtime=HttpxRuntime(httpx.AsyncClient(timeout=30)),
)
```

使用 `aiohttp`：

```python
from typact import AioHttpRuntime, HttpClient


client = HttpClient(
    "https://api.example.com",
    client_runtime=AioHttpRuntime(),
)
```

使用 Mock：

```python
from typact import HttpClient, MockRuntime, Path


runtime = MockRuntime()
runtime.add_response(
    "GET",
    "http://test.local/users/1",
    json_data={"id": 1, "name": "typact"},
)

client = HttpClient("http://test.local", client_runtime=runtime)


@client.get("/users/{user_id}")
async def get_user(user_id: int = Path()) -> dict:
    pass
```

## 拦截器

拦截器可以在请求发送前或响应转换前处理数据。

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

如果 token 会过期，可以使用 `CallableTokenProvider` 和 `RefreshableBearerTokenInterceptor`。

当请求返回 401 时，Typact 会调用 `refresh_token()` 刷新 token，并用新 token 自动重试一次。

```python
from typact import (
    CallableTokenProvider,
    HttpClient,
    InterceptorChain,
    RefreshableBearerTokenInterceptor,
)


async def login() -> str:
    # 在这里调用 /auth/login，并返回新的 token
    return "new-token"


token_provider = CallableTokenProvider(
    login,
    token="expired-token",
)

client = HttpClient(
    "https://api.example.com",
    interceptor_chain=InterceptorChain(
        request_interceptors=[
            RefreshableBearerTokenInterceptor(token_provider),
        ],
    ),
)
```

默认请求头是：

```text
Authorization: Bearer <token>
```

如果你的接口和一些内部系统一样，要求直接传 token：

```text
Authorization: <token>
```

可以设置 `scheme=None`：

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

文件名和媒体类型属于每次调用的数据，因此由 `FileData` 携带，而不是固定在
接口声明中。`content` 支持 `bytes` 和二进制文件对象；如果不需要指定文件名或
媒体类型，可以让接口接收 `bytes = File()` 并直接传入字节内容。

## 文件下载

将接口返回类型声明为 `bytes`，Typact 会直接返回原始响应体，不经过 JSON
解析或 Pydantic 转换：

```python
@client.get("/files/report.pdf")
async def download_file() -> bytes:
    pass


content = await download_file()
```

空文件会返回 `b""`。

## SSE

将返回类型声明为 `AsyncIterator[T]`，即可按 SSE 的 `data:` 事件持续接收并转换数据：

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

SSE 需要 `HttpxRuntime` 或 `AioHttpRuntime`；`MockRuntime` 支持通过
`add_sse_response()` 提供测试事件。

## 普通流式响应

接口返回 `AsyncIterator[bytes]` 会原样返回网络分片，适合大文件下载或转发；
声明为 `AsyncIterator[str]` 时会执行 UTF-8 增量解码：

```python
from collections.abc import AsyncIterator


@client.get("/files/report.zip")
async def download_report() -> AsyncIterator[bytes]:
    pass


async for chunk in download_report():
    await write_chunk(chunk)
```

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

Typact 的核心流水线是：

```text
Decorator
  -> RouteDefinition
  -> RequestBuilder
  -> InterceptorChain
  -> ClientRuntime
  -> ResponseConverter
```

每层只做一件事：

- Decorator 收集函数签名和返回类型。
- RequestBuilder 将调用参数转换成 `RequestConfig`。
- InterceptorChain 负责横切逻辑。
- Runtime 只负责发送请求并返回统一的 `Response`。
- ResponseConverter 只负责把响应转换成目标类型。

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

## License

本项目基于 [MIT License](LICENSE) 开源。
