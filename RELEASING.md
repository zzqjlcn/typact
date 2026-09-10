# 版本与发布流程

## 版本约定

- 使用 PEP 440 版本号，Git 标签固定为 `v<version>`，例如 `v0.2.1`、`v0.3.0a1`。
- `pyproject.toml` 是包版本的来源；主分支的版本号不等于已发布版本。
- 发布前将 Unreleased 条目整理为该版本的变更记录，说明兼容性与迁移事项。
- 优先先发布测试版本，再发布正式版本；测试版本不能设置为 GitHub Latest。
- 对 0.x 版本，兼容的新能力和修复可以采用补丁版本；破坏性 API 变化采用次版本并提供迁移说明。进入 1.0 后使用语义化版本规则。
- 不覆盖已有 PyPI 文件或移动已公开标签。版本号被占用时停止发布并重新确定版本。

## 发布检查

1. 确认版本范围、CHANGELOG、安装文档和工作区状态；CI 必须通过。
2. 查询 PyPI 对应版本的 JSON 接口，确认目标版本尚未占用。
3. 从待发布的明确提交构建，不混入未提交改动。每次使用空的独立输出目录。

```sh
uv sync --all-extras --group dev
uv run --no-sync pytest -q
uv build --out-dir .publish-dist
uv run --no-sync python scripts/check_dist.py .publish-dist
```

对该版本的 wheel 和 sdist 使用明确文件名执行 `uv run --no-sync twine check`，不要用通配符上传包含旧版本的目录。CI 还会单独安装 wheel，检查仅安装核心依赖时的导入和基本请求行为。

4. 在上述提交创建附注标签，并明确推送该标签至托管仓库。标签中的版本必须与该提交的 `pyproject.toml` 一致。
5. 使用下面的手动工作流准备 GitHub Draft Release；它不上传 PyPI，也不会发布 Release。
6. 使用已配置的 PyPI 凭据上传这两个已检查的文件。Windows 上设置 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8`，Twine 使用 `--non-interactive --disable-progress-bar`。不要将凭据放入仓库或日志。
7. 查询 PyPI JSON，验证版本、两个文件及 SHA-256；上传结果不确定时先核验，不能直接换版本重传。
8. 用已上传 PyPI 的相同产物更新 Draft Release 的附件，再公开 Release。稳定版设置 Latest，预发布设置 prerelease。分别核对 GitHub 与 AtomGit 的标签；仅核验后才能宣称两个托管平台已同步。

## GitHub Release 草稿

Actions 中手动运行 `Prepare release`，输入已存在的标签。工作流校验版本、运行测试并构建附件，创建或保留 Draft Release。对已公开 Release 不进行覆盖。

该工作流只适用于包含发布脚本和变更记录的新标签。历史标签的补录采用独立审计，不能自动重建并上传历史包。

## 历史版本修复

历史发行依据 PyPI JSON、原始 sdist 的 SHA-256 和 Git 源码比对确定，记录见 [release-history.json](docs/release-history.json)。源码比较只统一 CRLF/LF，不代表构建产物可逐字节重现。

版本号和源码都匹配的版本使用原提交；没有相符版本提交的发行从原始 PyPI sdist 建立独立恢复快照，不修改 main 的历史。恢复提交使用当前审计时间，Release 正文保留真实 PyPI 发布时间及恢复说明。

历史 Release 附件使用 PyPI 原始文件，不使用当下环境重新构建的包。未发布的 0.2.2 不补正式标签或 Release。
