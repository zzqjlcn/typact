---
layout: ../../layouts/DocsLayout.astro
title: Getting started
description: Install Typact and make your first typed HTTP request in five minutes.
---

# Getting started

Install Typact and make your first declarative, type-safe HTTP request in five minutes.

## Install

The core package depends only on Pydantic. Its default Runtime uses Python's standard library, so a separate HTTP client is optional.

```bash
pip install typact
```

Install the corresponding extra to use httpx or aiohttp:

```bash
pip install "typact[httpx]"
pip install "typact[aiohttp]"
```

> Typact supports Python 3.10 through 3.14.

## Declare an endpoint

Create a response model and client, then describe the remote endpoint with a decorator:

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

The function body stays empty. Typact reads the signature, builds the request, and converts the response into `User`.

## Make a request

The decorated function is now an async callable:

```python
user = await get_user(1)
print(user.name)

await client.close()
```

Continue with [parameter annotations](/docs/annotations/) or [core concepts](/docs/concepts/).

## Add production policies

Configure shared timeouts and retries when you create the client:

```python
from typact import HttpClient, RetryConfig


client = HttpClient(
    "https://api.example.com",
    timeout=10,
    retry_config=RetryConfig(max_retries=3),
)
```

Retries are disabled by default. When enabled, the default policy retries idempotent requests only, avoiding accidental duplicate writes.
