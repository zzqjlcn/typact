---
layout: ../../layouts/DocsLayout.astro
title: 参数注解
description: 使用 Path、Query、Header、Cookie、Body、Form 和 File 构建请求。
---

# 参数注解

使用明确的参数注解描述每个值在 HTTP 请求中的位置。

## Path 与 Query

```python
from typact import HttpClient, Path, Query

@client.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(),
    details: bool = Query(False),
) -> User:
    pass
```

`alias` 可以让 Python 参数名与线上的字段名解耦：

```python
page_size: int = Query(20, alias="pageSize")
```

## Header 与 Cookie

```python
request_id: str = Header(alias="X-Request-Id")
session: str = Cookie(alias="session_id")
```

## Body 与 Form

```python
@client.post("/users")
async def create_user(payload: UserInput = Body()) -> User:
    pass

@client.post("/auth/login")
async def login(name: str = Form(), password: str = Form()) -> Token:
    pass
```

## File

文件参数会被构建成 Runtime 可以直接消费的 multipart 数据：

```python
@client.post("/upload")
async def upload(
    content: bytes = File(alias="file", filename="report.txt", content_type="text/plain"),
) -> dict:
    pass
```
