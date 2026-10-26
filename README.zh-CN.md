# Repoize

**从仓库事实生成并维护 AI 编程配置。**

提取项目已有信息，生成 `AGENTS.md` 和选定工具配置；查看问题与命令依据，预览更新，保留团队手写说明。

[English](README.md) · [使用样例](examples/README.zh-CN.md) · [支持范围](docs/support.zh-CN.md) · [升级迁移](docs/migration.zh-CN.md) · [贡献指南](CONTRIBUTING.zh-CN.md)

[![PyPI](https://img.shields.io/pypi/v/repoize.svg)](https://pypi.org/project/repoize/)
[![Python](https://img.shields.io/pypi/pyversions/repoize.svg)](https://pypi.org/project/repoize/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 本文对应 **0.3.0 开发源码**。2026-10-26 核对时，PyPI 公开包仍为 **0.1.0**，不包含下面的新命令。试用本轮功能请从源码安装；选择安装包前检查 [Release 列表](https://github.com/LQDC3417/repoize/releases)。

## 在已有项目试用

需要 Python 3.10+；源码安装还需 Git。建议使用虚拟环境或独立工具安装器。

```bash
python -m pip install "git+https://github.com/LQDC3417/repoize.git"

# 只读：检查配置与命令依据。
repoize doctor /path/to/project

# 只读：查看默认生成计划。
repoize init /path/to/project --dry-run

# 创建 AGENTS.md；已有文件跳过。
repoize init /path/to/project
```

若已安装 [uv](https://docs.astral.sh/uv/)，也可一次性运行源码版本：

```bash
uvx --from "git+https://github.com/LQDC3417/repoize.git" repoize doctor /path/to/project
```

公开稳定包使用 `python -m pip install repoize`，命令能力以该安装版本的 `--help` 为准。

## 能解决什么

- **说明命令依据。** 区分项目声明、配置推导和通用建议；提取成功不代表执行或验证通过。
- **定位具体问题。** 每条诊断包含规则、文件、依据和下一步。只用 Cursor 的项目无需补齐 Claude、MCP 或 Skill。
- **审阅并维护。** 预览与写入共用候选内容；普通更新保留手写区和已有 frontmatter，无变化不重写。
- **默认输出克制。** `init` 只生成 `AGENTS.md`，MCP、Skill 显式选择。默认不扫描本机环境变量、不执行项目脚本、不上传代码、不调用模型。

查看[真实本地演示](examples/README.zh-CN.md)：中英文生成文件，以及保留手写说明的更新过程。

## 选择生成内容

```bash
# AGENTS.md 加 Claude 指令。
repoize init /path/to/project --type claude

# 仅生成明确选择的类型。
repoize generate /path/to/project --type cursor --type copilot

# 中文生成；后续更新传入相同语言。
repoize init /path/to/project --lang zh

# 可选 MCP 空模板与项目 Skill。
repoize generate /path/to/project --type mcp --type skill
```

| 类型 | 生成路径 |
| --- | --- |
| `agents` | `AGENTS.md` |
| `claude` | `CLAUDE.md` |
| `cursor` | `.cursor/rules/repoize.mdc` |
| `copilot` | `.github/copilot-instructions.md` |
| `mcp` | `.mcp.json` |
| `skill` | `.claude/skills/project-dev/SKILL.md` |

保留 `cursorrules` 作为 `cursor` 别名。旧路径会被发现，但不自动迁移；已有配置先阅读[手动迁移说明](docs/migration.zh-CN.md)。

MCP 只生成空 `mcpServers`，不替用户选择、安装或启动服务。诊断明确提示尚无服务器。添加前阅读 [MCP 示例](examples/mcp/README.zh-CN.md)。

## 检查与更新

```bash
repoize doctor /path/to/project --type cursor --strict
repoize doctor /path/to/project --format json
repoize update /path/to/project --dry-run
repoize update /path/to/project --dry-run --diff
repoize update /path/to/project
repoize update /path/to/project --check
```

普通更新只处理上表固定生成路径中的已有文件，不补建缺失文件，也不认领任意自定义规则。Doctor 可检查其他受支持的规则或 Skill，但不因此取得写入所有权。标记区间外文字和已有 frontmatter 归用户维护。无效文件、损坏标记、旧配置冲突和不安全路径会报错，不静默覆盖。

生成时 `--force` 替换合法当前目标的整份内容，包括手写说明或 MCP 服务定义。先使用 `--force --dry-run` 查看替换。Force 不绕过迁移和路径保护。

旧文件可能含私有内容，文本差异须显式加 `--diff`；MCP 只列字段路径，不展示秘密值。后续命令重新读取与计算，预览不保存批准事务。

漂移检查比较受管正文，不比较手写编辑或用户维护的 MCP 定义；没有可比较内容时不能通过。语言选择与退出码见 [CI 示例](docs/ci.zh-CN.md)。

## 分析与 JSON

```bash
repoize analyze /path/to/project
repoize analyze /path/to/project --format json --output analysis.json
repoize validate analysis.json
# 显式平台与工具版本，不收集环境变量值。
repoize analyze /path/to/project --include-env
```

分析 JSON v1 继续与 `validate` 配对；doctor 和变更报告使用独立 Schema。JSON 标准输出只有数据，状态信息写入 stderr。分析报告仍含项目路径，分享前需要检查。

来源分类、提取边界和规则编号见[命令证据与诊断规则](docs/command-evidence.zh-CN.md)。

旧 `check` 保留配置覆盖报告语义，不作为 CI 阻断。分数反映检测到的工程配置，不证明代码正确、客户端已加载或模型遵守。具体问题使用 `doctor`，受管内容漂移使用 `update --check`。

## 适用场景与相关工具

需要提取仓库已有开发事实，并让生成上下文随项目变化维护时，使用 Repoize。

已有团队规则需要分发到多种工具，可对照 [Rulesync](https://github.com/dyoshikawa/rulesync)、[Ruler](https://github.com/intellectronica/ruler)。源码打包可对照 [Repomix](https://github.com/yamadashy/repomix)、[Gitingest](https://github.com/coderamp-labs/gitingest)，工作流可以互补。

现有画像覆盖 Python、JavaScript、TypeScript、Go、Rust、Java、Ruby、PHP，不代表理解所有构建系统或框架。[支持范围](docs/support.zh-CN.md)区分格式检查与客户端实测。

## 开发与反馈

```bash
git clone https://github.com/LQDC3417/repoize.git
cd repoize
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src/ tests/ scripts/
python -m ruff format --check src/ tests/ scripts/
```

欢迎提交最小误识别声明文件、命令来源回归或客户端发现记录。样例应公开或脱敏，不上传令牌和专有指令。参见[贡献指南](CONTRIBUTING.zh-CN.md)、[执行路线](docs/superpowers/plans/2026-10-26-repoize-roadmap.md)、[发布准备](docs/releasing.md)。

MIT 许可证，详见 [LICENSE](LICENSE)。
