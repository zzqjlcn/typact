---
layout: ../../layouts/DocsLayout.astro
title: Parameter annotations
description: Build requests with Path, Query, Header, Cookie, Body, Form, and File.
---

# Parameter annotations

Use explicit annotations to describe where every value belongs in an HTTP request.

## Path and Query

```python
from typact import HttpClient, Path, Query


@client.get("/users/{user_id}")
async def get_user(
    user_id: int = Path(),
    details: bool = Query(False),
) -> User:
    pass
```

Use `alias` when the Python parameter name and wire name should differ:

```python
page_size: int = Query(20, alias="pageSize")
```

## Header and Cookie

```python
request_id: str = Header(alias="X-Request-Id")
session: str = Cookie(alias="session_id")
```

## Body and Form

```python
@client.post("/users")
async def create_user(payload: UserInput = Body()) -> User:
    pass


@client.post("/auth/login")
async def login(name: str = Form(), password: str = Form()) -> Token:
    pass
```

## File

File parameters become multipart data that the selected Runtime can send directly:

```python
@client.post("/upload")
async def upload(
    content: bytes = File(
        alias="file",
        filename="report.txt",
        content_type="text/plain",
    ),
) -> dict:
    pass
```
