# 贡献指南

Typact 是开源 HTTP 客户端库。设计变更应考虑通用场景、公共 API、可选依赖、不同 Runtime 的一致性，以及已有用户的升级成本。

## 开发环境

Python 3.13 或 3.14；使用 uv 管理环境：

```sh
uv sync --all-extras --group dev
uv run --no-sync pytest -q
```

CI 在 Windows 和 Linux 上运行上述两个 Python 版本的完整测试，包含 urllib、httpx 和 aiohttp。Python 元数据允许更新版本，但未经 CI 验证的版本不在当前保证范围内。

文档使用 Node.js 22，版本记录在 `docs-site/.node-version`：

```sh
cd docs-site
npm ci
npm run build
```

标准静态构建不需要 Sites 配置；仅在已配置 `.openai/hosting.json` 的专用环境中使用 `npm run build:sites`。Netlify 使用同一标准构建命令。Windows 上请使用约定的 Node 22，避免已观察到的 Node 24.19.0 退出断言。

## 提交要求

- 每次变更聚焦一个问题，新增公开行为需补文档和边界测试。
- 修改重试、认证、超时、取消或流式行为时，说明组合语义与资源生命周期。
- 保持可选 HTTP 依赖可选；核心安装不可因新增功能而强制导入它们。
- 将用户可见变化写入 `CHANGELOG.md` 的 Unreleased 部分。
- 公共 API 的删除、更名或默认语义变化必须说明迁移方式；不要用实现更简单作为唯一理由。
- 不提交凭据、依赖缓存或生成的构建产物。不要改写已公开的版本标签。

发布流程见 [RELEASING.md](RELEASING.md)。
