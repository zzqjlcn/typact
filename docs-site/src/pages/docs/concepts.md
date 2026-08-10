---
layout: ../../layouts/DocsLayout.astro
title: 核心概念
description: 理解 Typact 如何把函数签名编译为 HTTP 请求。
---

# 核心概念

Typact 把 Python 函数签名视为一份可执行的 HTTP 契约。

## 一条清晰的流水线

每次调用都会依次经过四个阶段：**读取声明 → 构建请求 → Runtime 传输 → 响应转换**。各阶段只负责一件事，因此可以独立替换和测试。

| 阶段 | 职责 |
| --- | --- |
| Client | 保存基础地址、路由元数据和共享配置 |
| Builder | 将参数注解转换为 URL、Header 与请求体 |
| Runtime | 真正发送请求，不参与业务建模 |
| Converter | 根据返回类型转换响应数据 |

## 函数签名就是契约

```python
@client.post("/teams/{team_id}/members")
async def add_member(
    team_id: int = Path(),
    notify: bool = Query(True),
    payload: MemberInput = Body(),
) -> Member:
    pass
```

路径、查询参数、请求体与响应模型集中在一个位置，编辑器和类型检查器可以完整理解这份契约。

## 可插拔，而非绑定

Typact 的核心不依赖某个 HTTP 库。`UrllibRuntime` 负责零依赖默认体验，`HttpxRuntime` 与 `AioHttpRuntime` 提供不同生态选择，也可以实现自己的 Runtime。
