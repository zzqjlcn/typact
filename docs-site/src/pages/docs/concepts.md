---
layout: ../../layouts/DocsLayout.astro
title: Core concepts
description: Understand how Typact compiles a function signature into an HTTP request.
---

# Core concepts

Typact treats a Python function signature as an executable HTTP contract.

## One clear pipeline

Every call passes through four stages: **read the declaration → build the request → run the transport → convert the response**. Each stage has one responsibility, so it can be replaced and tested independently.

| Stage | Responsibility |
| --- | --- |
| Client | Holds the base URL, route metadata, and shared configuration |
| Builder | Converts parameter annotations into the URL, headers, and body |
| Runtime | Sends the request without owning business models |
| Converter | Converts response data according to the declared return type |

`AsyncIterator[bytes]` and `AsyncIterator[str]` preserve raw stream semantics. Other `AsyncIterator[T]` declarations represent Server-Sent Events and convert each `data:` payload into `T`.

## The function signature is the contract

```python
@client.post("/teams/{team_id}/members")
async def add_member(
    team_id: int = Path(),
    notify: bool = Query(True),
    payload: MemberInput = Body(),
) -> Member:
    pass
```

The path, query parameters, body, and response model live in one place that editors and type checkers can understand.

## Pluggable instead of coupled

Typact's core does not depend on one HTTP library. `UrllibRuntime` provides a zero-extra-dependency default, while `HttpxRuntime` and `AioHttpRuntime` integrate with their respective ecosystems. Applications can also provide a custom Runtime.
