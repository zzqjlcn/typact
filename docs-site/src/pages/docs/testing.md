---
layout: ../../layouts/DocsLayout.astro
title: 测试
description: 使用 Mock Runtime 验证请求构建，无需启动真实服务。
---

# 测试

Mock Runtime 让测试聚焦在“声明是否生成了正确请求”，无需网络或真实后端。

## 为什么使用 Mock Runtime

常规 HTTP Mock 往往发生在网络层。Typact 的 Mock Runtime 直接替换传输边界，因此测试更快、更确定，也更容易检查请求配置。

## 基本测试

```python
from typact import HttpClient, MockRuntime, Query

runtime = MockRuntime()
runtime.add_response(
    "GET",
    "https://api.example.com/items",
    json_data={"items": []},
)
client = HttpClient("https://api.example.com", client_runtime=runtime)

@client.get("/items")
async def list_items(page: int = Query(1)) -> dict:
    pass

result = await list_items(page=2)
assert result == {"items": []}
assert runtime.requests[0].params == {"page": 2}
```

## 流与 SSE

Mock Runtime 也能为流式路由提供确定性的分片数据：

```python
runtime.add_stream_response(
    "GET",
    "https://api.example.com/download",
    [b"first", b"-second"],
)

runtime.add_sse_response(
    "GET",
    "https://api.example.com/events",
    ['data: {"value": 1}\n\n'],
)
```

普通流使用 `add_stream_response()`；SSE 使用 `add_sse_response()`。测试时应断言转换后的事件或分片，而不依赖真实网络时序。

## 测试边界

建议分别验证 URL 与参数构建、认证和 Trace 拦截器、响应类型转换，以及文件上传等容易出错的边界。
