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
