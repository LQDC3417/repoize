<div align="center">

# 🤖 Repoize

**一条命令让任何项目对 AI Agent 友好**

[![PyPI version](https://img.shields.io/pypi/v/repoize.svg)](https://pypi.org/project/repoize/)
[![Python Versions](https://img.shields.io/pypi/pyversions/repoize.svg)](https://pypi.org/project/repoize/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/repoize)](https://pepy.tech/project/repoize)

[English](#english) | [中文](#中文)

</div>

---

<a name="中文"></a>
## 🚀 一键生成 AI Agent 配置文件

自动生成 [AGENTS.md](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)、`CLAUDE.md`、`.cursorrules`、MCP Server 配置、Skill 文件，让 Claude Code、Cursor、Copilot 等 AI 编程助手立即理解你的项目。

### ✨ 特性

- 🔍 **智能分析** — 自动检测语言、框架、依赖、构建命令
- 📊 **代码质量** — 分析代码质量，检测质量工具和配置
- 🔄 **增量更新** — 保留手写内容，只更新生成区间
- 🛡️ **隐私安全** — 纯本地分析，自动过滤敏感环境变量
- 🌐 **多语言支持** — Python、JavaScript、TypeScript、Go、Rust、Java、Ruby、PHP

### 📦 安装

```bash
pip install repoize
```

### 🎯 快速开始

```bash
# 一键扫描 + 生成所有配置文件
repoize init

# 查看项目分析报告（含代码质量分析）
repoize analyze

# 选择性生成配置文件
repoize generate --type agents --type claude --type cursorrules

# 检查项目 Agent 就绪度
repoize check

# 增量更新配置
repoize update
```

### 📋 支持的配置文件

| 配置文件 | 用途 |
|---------|------|
| `AGENTS.md` | 通用 Agent 指令 |
| `CLAUDE.md` | Claude Code 专属指令 |
| `.cursorrules` | Cursor AI 规则 |
| `.github/copilot-instructions.md` | GitHub Copilot 指令 |
| `.claude/mcp.json` | MCP Server 配置 |
| `.claude/skills/*/SKILL.md` | 项目专属 Skill 文件 |

### 📊 代码质量分析

Repoize 不仅生成配置文件，还能分析项目的代码质量：

```
代码质量: 优秀 (100/100)

代码统计:
  文件数: 39
  总行数: 3,668
  代码行: 2,929
  质量工具: pytest, ruff
  质量配置: pyproject.toml
```

### 🔧 高级用法

```bash
# 输出 JSON 格式的分析结果
repoize analyze --format json --output analysis.json

# 校验 JSON 输出是否符合 Schema
repoize validate analysis.json

# 跳过环境变量扫描
repoize analyze --no-env

# 强制覆盖已有文件
repoize init --force
```

### 脚本集成与安全更新（v0.1.1）

- `analyze --format json` 的标准输出只包含 JSON；状态提示写入标准错误。使用 `--output` 时，JSON 写入文件，标准输出为空。
- `init`、`generate`、`update` 全部成功或正常跳过时返回 `0`；任一文件处理失败时返回 `1`，并继续处理其他文件。`html` 格式尚未实现，会返回参数错误。
- `update` 保留文本生成区间外的手写内容和换行；相同分析结果重复更新不会增加空行。
- MCP JSON 更新补充缺失项，已有同名字段优先保留，冲突时提示；无效 JSON 会报错并保留原文件。需要完全重新生成时，使用 `generate --type mcp --force`，这会覆盖整个 MCP 文件。

### 📁 示例输出

运行 `repoize analyze` 后的输出示例：

```
┌───────────────────────────── 📊 项目健康度报告 ─────────────────────────────┐
│ my-project                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

语言: Python (主)
语言画像: Python
框架: fastapi, sqlalchemy

Agent 就绪度: 完备 (100/100)
代码质量: 优秀 (85/100)

┌─────────────────────────────────────┬───────────┬──────────────────────┐
│ 配置文件                            │   状态    │ 说明                 │
├─────────────────────────────────────┼───────────┼──────────────────────┤
│ AGENTS.md                           │ ✅ 已配置 │ 通用 Agent 指令      │
│ CLAUDE.md                           │ ❌ 未配置 │ Claude Code 专属指令 │
│ .cursorrules                        │ ❌ 未配置 │ Cursor AI 规则       │
└─────────────────────────────────────┴───────────┴──────────────────────┘
```

### 🛠️ 开发

```bash
# 克隆仓库
git clone https://github.com/LQDC3417/repoize.git
cd repoize

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check src/ tests/
ruff format --check src/ tests/
```

### 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<a name="english"></a>
## 🚀 Make Any Project AI Agent Friendly

Auto-generate [AGENTS.md](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot), `CLAUDE.md`, `.cursorrules`, MCP Server config, and Skill files to help Claude Code, Cursor, Copilot and other AI coding assistants understand your project instantly.

### ✨ Features

- 🔍 **Smart Analysis** — Auto-detect languages, frameworks, dependencies, and build commands
- 📊 **Code Quality** — Analyze code quality, detect quality tools and configurations
- 🔄 **Incremental Updates** — Preserve handwritten content, only update generated sections
- 🛡️ **Privacy Safe** — Pure local analysis, auto-filter sensitive environment variables
- 🌐 **Multi-language** — Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, PHP

### 📦 Installation

```bash
pip install repoize
```

### 🎯 Quick Start

```bash
# Scan + generate all config files
repoize init

# View project analysis report (with code quality)
repoize analyze

# Generate specific config files
repoize generate --type agents --type claude --type cursorrules

# Check project agent readiness
repoize check

# Incremental update
repoize update
```

### 📋 Supported Config Files

| Config File | Purpose |
|-------------|---------|
| `AGENTS.md` | General Agent instructions |
| `CLAUDE.md` | Claude Code specific instructions |
| `.cursorrules` | Cursor AI rules |
| `.github/copilot-instructions.md` | GitHub Copilot instructions |
| `.claude/mcp.json` | MCP Server config |
| `.claude/skills/*/SKILL.md` | Project-specific Skill files |

### 📄 License

MIT License - see [LICENSE](LICENSE) for details

### Scripting and safe updates (v0.1.1)

- `analyze --format json` writes only JSON to stdout and status messages to stderr. With `--output`, the JSON is written to the file and stdout stays empty.
- `init`, `generate`, and `update` return `0` on success or normal skips, and `1` if any file fails; other files are still processed. The unavailable `html` format returns a usage error.
- Text updates preserve content and line endings outside the generated markers. Repeating an update with the same analysis does not add blank lines.
- MCP updates add missing fields and keep existing values, warning on conflicts. Invalid JSON is reported without overwriting the file. To regenerate the entire MCP file, use `generate --type mcp --force`; this replaces its existing contents.

---

<div align="center">

**[⬆ Back to top](#🤖-repoize)**

</div>
