---
layout: ../../layouts/DocsLayout.astro
title: Interceptors
description: Add authentication, logging, and tracing without changing endpoint contracts.
---

# Interceptors

Interceptors add behavior before or after a request without mixing infrastructure into endpoint declarations.

## Common uses

- Add authentication headers
- Log requests and responses
- Inject trace IDs
- Collect latency and status metrics

## Configure authentication

```python
from typact import BearerTokenInterceptor, HttpClient, InterceptorChain


client = HttpClient(
    "https://api.example.com",
    interceptor_chain=InterceptorChain(
        request_interceptors=[BearerTokenInterceptor("your-token")],
    ),
)
```

Multiple interceptors run as a chain in configuration order. Endpoint functions continue to describe business inputs and outputs only.

## Custom interceptors

Implement the request or response extension point on the base interceptor to package application-specific behavior. Keep reusable policies in interceptors instead of repeating them in every endpoint function.
