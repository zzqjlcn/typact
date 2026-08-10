---
layout: ../../layouts/DocsLayout.astro
title: 快速开始
description: 安装 Typact，并在五分钟内完成第一个类型安全的 HTTP 请求。
---

# 快速开始

安装 Typact，并在五分钟内完成第一个声明式、类型安全的 HTTP 请求。

## 安装

核心包只依赖 Pydantic，默认 Runtime 使用 Python 标准库，无需额外安装 HTTP 客户端。

```bash
pip install typact
```

需要 `httpx` 或 `aiohttp` 时安装对应扩展：

```bash
pip install "typact[httpx]"
pip install "typact[aiohttp]"
```

> Typact 当前要求 Python 3.13 或更高版本。

## 定义第一个接口

创建响应模型和 Client，然后用装饰器声明远程 API：

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
```

函数体保持为空。Typact 会读取函数签名，构建请求并将响应转换为 `User`。

## 发起请求

声明后的函数就是可直接调用的异步函数：

```python
user = await get_user(1)
print(user.name)

await client.close()
```

下一步，了解 [参数注解](/docs/annotations/) 或 Typact 的 [核心概念](/docs/concepts/)。
