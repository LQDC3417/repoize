# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

### Changed

- `init` now creates only `AGENTS.md` by default; repeat `--type` to add client targets. `generate` requires explicit types and writes only those targets.
- `cursor` is the canonical type; `cursorrules` remains an alias. Repeated types are deduplicated.
- `update` only handles existing Repoize targets and reports explicitly requested missing files with a `generate` hint. Legacy paths still require manual migration.
- `init`, `generate`, and `update` accept `--lang en|zh` (default: English). Updates preserve handwritten content and existing frontmatter.
- Generated commands now require declared or inferred local evidence, include source locations, and are marked as not executed. Language-profile suggestions are excluded from generated instructions.
- Existing targets are skipped without an interactive prompt. Selection, migration, format, and path safeguards still apply with `--force`.

### Added

- Read-only `doctor` diagnostics for local configuration formats and command evidence, with a separate versioned JSON report.

## [0.1.2] - Unreleased

### Changed

- MCP 默认输出根目录 `.mcp.json`，仅包含空 `mcpServers`；不配置、安装或启动默认服务
- Cursor 输出 `.cursor/rules/repoize.mdc`，保留 `cursorrules` CLI 类型名
- Skill 固定使用 `project-dev` 名称，移除未经确认的 MIT 声明；Skill 与 Cursor frontmatter 位于首行，managed marker 仅包围正文
- 所有命令默认关闭环境扫描；`analyze --include-env` 仅收集平台和排序的工具版本，不收集环境变量值、shell 路径或 PATH；`--no-env` 保持兼容
- 生成模板不再包含本机环境信息、作者语言偏好或无依据的部署承诺；候选命令提示使用前核对
- 人类报告将评分标为配置覆盖与工程配置参考，analysis JSON v1 字段结构保持不变

### Fixed

- 安全解析 YAML 并验证 Skill/Cursor 元数据，更新时逐字保留合法 frontmatter 与未知字段
- 拒绝不完整、重复、逆序或嵌套 marker，保留手写前后缀、BOM、LF/CRLF；相同内容不写盘
- 拒绝目录、符号链接、Windows junction 和项目外输出目标；`--force` 不绕过保护
- MCP 增量更新保留未知 JSON 字段与完整服务器定义，避免拼接同名服务；`--force` 完整覆盖合法当前目标；无效 JSON 不写入
- 统一 init/generate/update 的旧配置迁移决策：仅旧文件时失败；MCP 新旧并存仅处理新文件并告警，仍按生成跳过/force 覆盖/增量更新规则执行；Cursor 并存阻断；旧 Skill 包装格式要求手动迁移
- 扫描识别新旧路径、递归 Cursor 规则与 Skill 文件，目录不再算配置文件，同类不重复加分
- 测试检测不再把语言画像的建议命令或空测试目录当作实际测试证据

## [0.1.1] - Unreleased

### Fixed

- JSON 标准输出不再混入状态提示，保留长路径和方括号等原始内容
- init、generate、update 任一文件失败时返回非零状态，同时继续处理其他文件并汇总失败数
- 无效 MCP JSON 和读取错误明确报告，不覆盖原文件
- 重复文本更新不再累积空行，保留手写前后缀及 LF/CRLF 换行
- 使用真实 TOML 解析依赖和工具配置，支持单引号、extras、多行数组和注释
- Python console script 使用注册命令名，避免生成不可执行的模块命令
- Python 3.10 通过条件依赖 tomli 保持 TOML 检测能力
- HTML 格式尚未实现时返回明确错误，而非成功状态

### Changed

- JSON 模式的状态提示改写 stderr；MCP 更新优先保留已有值，冲突时给出提示
- CI 增加 Windows 测试及隔离安装 wheel 后的完整 CLI 冒烟验证

## [0.1.0] - 2026-08-07

### Added

- 初始发布版本
- 支持 8 种编程语言：Python、JavaScript、TypeScript、Go、Rust、Java、Ruby、PHP
- 自动生成 6 种配置文件：AGENTS.md、CLAUDE.md、.cursorrules、Copilot 指令、MCP 配置、Skill 文件
- 项目分析功能：语言检测、框架检测、依赖解析、命令提取
- 代码质量分析：代码统计、质量评分、工具检测
- 健康报告：Agent 就绪度评分、代码质量评分
- 增量更新：保留手写内容，只更新生成区间
- JSON 输出：支持 Schema 校验
- 敏感环境变量自动过滤
- 并行工具检测优化性能
- 完整的测试覆盖（97 个测试）
- 贡献指南（CONTRIBUTING.md）
- GitHub Release 自动化发布流程

### Fixed

- 打破 language_profiles 和 dep_parser 之间的循环依赖
- 添加 health_report.py 返回类型注解
- 优化 cli.py 异常处理：捕获更具体的异常类型
- 优化 quality_analyzer.py 静默异常处理
- 补充 config_scanner.py 完整测试覆盖
- 统一代码格式（移除 BOM，修复尾随空行）

### Changed

- 更新测试数量：从 62 个增加到 97 个
- 更新 CI/CD 配置：支持 Python 3.10-3.13
- 更新文档：添加中英文双语 README

## [Unreleased]

### Added

- 计划：交互式CLI向导（`repoize wizard`）
- 计划：配置持久化（`.repoize.toml`）
- 计划：进度条显示
- 计划：HTML分析报告
- 计划：自定义模板目录
- 计划：Mermaid依赖关系图表
- 计划：多项目批量分析
