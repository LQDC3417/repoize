# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
