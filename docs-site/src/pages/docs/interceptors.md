---
layout: ../../layouts/DocsLayout.astro
title: 拦截器
description: 用拦截器扩展认证、日志和链路追踪。
---

# 拦截器

拦截器在不污染接口声明的前提下，为请求前后增加横切能力。

## 典型用途

- 添加认证 Header
- 记录请求与响应日志
- 注入 Trace ID
- 统一收集耗时与状态

## 配置认证

```python
from typact import AuthInterceptor, HttpClient

client = HttpClient(
    "https://api.example.com",
    interceptors=[AuthInterceptor(token="your-token")],
)
```

多个拦截器会按配置顺序组成链。接口函数仍然只描述业务输入与输出。

## 自定义拦截器

继承基础拦截器并实现请求前或响应后的扩展点，即可封装项目级行为。把可复用的策略放在拦截器中，而不是重复写进每个接口函数。
