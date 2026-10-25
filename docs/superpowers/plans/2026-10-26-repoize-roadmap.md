# Repoize v0.1.2–v0.3.0 Implementation Plan

> **For agentic workers:** Use subagent-driven-development task by task, with specification review followed by quality review. Do not publish packages, tags, releases, or repository settings without separate authorization.

**Goal:** 从仓库事实生成、解释、检查并安全维护 AI 编程配置。

**Architecture:** 复用现有分析器、生成器与模板。命令证据保留在内部模型，doctor 使用独立报告；预览、漂移检查和写入共享同一候选内容计算。旧分析 JSON v1 不变形。

**Tech Stack:** Python 3.10+、Click、Rich、Jinja2、JSON Schema、PyYAML safe loader、pytest、Ruff。

## 已确认的产品决定

- 面向个人开发者和小团队，分三个版本交付，不承诺 star 增长。
- v0.1.2 修兼容与可信度；v0.2.0 增加 doctor、证据、最小默认及双语；v0.3.0 增加预览和漂移检查。
- v0.2.0 起 init 默认仅 AGENTS.md；init --type 增加类型，generate --type 只生成所选类型。
- MCP、Skill 显式选择；MCP 生成空 mcpServers 对象，服务配置通过文档示例提供，不安装或启动服务。
- 默认关闭本机环境扫描；--no-env 保持兼容；只有 analyze --include-env 可扫描工具版本和平台，不收集环境变量值与 PATH。
- 默认英文生成，init/generate/update --lang en|zh；用户手写内容和已有 frontmatter 不翻译。
- 英文主 README、完整中文 README；CLI 新帮助及诊断英文，中文文档解释。
- 旧配置只识别、提示并指导手动迁移；前三版无自动迁移命令。
- 第三版包括 update --check 和普通 GitHub Actions 示例，不维护独立 Action。
- 无默认遥测、仓库上传、模型接口、项目脚本执行或隐藏状态文件。

## 公共接口合同

- 保留 analyze/validate 的 JSON v1、commands 五组字符串数组和旧字段形状。
- doctor [path] --type TYPE（可重复）--format terminal|json --strict。
- cursor 为新类型名，cursorrules 为兼容别名，处理时去重。
- doctor 自动模式只检查发现的配置；显式类型缺入口为 error；无任何配置给 warning，不冒充全部通过。
- doctor JSON: report_type=doctor、schema_version=1、selected_types、findings、command_evidence、summary；独立 schema。
- Diagnostic: rule_id、severity、type、path（相对路径或 null）、message、evidence、suggestion。
- 命令来源 declared/inferred/suggested，执行状态 not_run；同一命令保留多个来源，不使用伪置信度。
- doctor 退出码：0 无 error；1 有 error 或 strict 下有 warning；2 参数错误；3 无法完成检查。
- check 保持旧退出语义，只作兼容报告，不改为 CI 阻断。
- v0.2.0 起 update 只更新已有配置；显式类型缺失时失败并提示 generate，不自动补建。
- init/generate/update --dry-run；--diff 仅终端预览；--format terminal|json（写入/预览报告）。
- 变更 JSON: report_type=changes、schema_version=1、mode、changes、summary；不包含原始字节或秘密值；独立 schema。
- FileChange 动作 create/update/unchanged/skip/conflict/error；旧/新字节只在内部使用。
- update --check 退出码：0 一致；1 漂移或内容冲突；2 参数错误；3 无效文件、运行失败或无可比较内容。
- 普通写入退出码保持 0 成功或正常跳过、1 处理失败、2 参数错误。
- --dry-run 与 --check 互斥；--diff 需要 dry-run，不能配 JSON。
- 预览与实际调用独立重新计算；输入不变时候选字节一致，不保存跨调用的批准快照。

## Task 1 — v0.1.2 兼容和安全基础

- [ ] 回归先行：旧路径、新路径、旧包装 Skill、损坏 marker、BOM/CRLF、合成凭据、默认测试误报。
- [ ] MCP 新路径 .mcp.json，内容 {"mcpServers": {}}，JSON 序列化生成。
- [ ] Cursor 新路径 .cursor/rules/repoize.mdc；首部 description 和 alwaysApply:true，不猜 globs。
- [ ] Skill 路径 .claude/skills/project-dev/SKILL.md，name:project-dev，删除无依据 license。
- [ ] 完整文件渲染和仅 managed body 替换分离；更新不重复 header，原 frontmatter 保留并校验。
- [ ] 仅一对顺序正确 marker 可更新；缺失视为不受管，重复/逆序/嵌套报错。
- [ ] 原文件无效、不受管、是目录或指向项目外的链接时不覆盖。
- [ ] 旧路径独存：该类型要求手动迁移，不创建副本；新旧 MCP 并存只处理新路径并告警；Cursor 并存阻断该类型。
- [ ] JSON 保留未知字段和完整现有服务器定义，不拼接不同同名服务器的字段。
- [ ] 默认环境关闭；显式 include-env 仅平台和排序后的工具版本；共享模板不写本机环境。
- [ ] has_tests 不由 profile 建议命令证明；有依据才生成测试结论。
- [ ] 移除跨项目模板的作者偏好、无依据授权和强制命令。
- [ ] 报告不把存在性分数当有效性或真实质量；保留 v1 JSON 兼容字段。
- [ ] 更新相关测试、安装冒烟、版本 0.1.2、CHANGELOG；pytest/Ruff/隔离包验证。
- [ ] Specification review -> 修复 -> quality review -> 修复 -> 本地阶段提交。

## Task 2 — 命令证据与只读 doctor

- [ ] CommandSet 增加内部证据，但 to_dict() 保持 v1 字符串数组。
- [ ] 命令来源包括相对文件、selector、kind；全部 not_run，多来源去重。
- [ ] 缺 dev extra 不声称 .[dev]；JS 优先 packageManager，其次唯一锁文件，冲突告警。
- [ ] 保留旧分析的容错路径，doctor 区分文件缺失、语法错误、编码错误、权限错误。
- [ ] 实现 CFG001–CFG007、UPD001、SRC001、CMD001–CMD002；稳定排序，内容不回显秘密值。
- [ ] doctor 不启动子进程、不写文件、不扫描环境、不读取项目外配置。
- [ ] 独立 doctor schema、纯 JSON stdout、进度 stderr、参数和退出码回归。
- [ ] Specification review -> 修复 -> quality review -> 修复。

## Task 3 — v0.2.0 最小默认与双语

- [ ] init 默认 AGENTS，init --type 在此基础增加；generate 精确选择；cursor/cursorrules 别名去重。
- [ ] update 不创建缺失文件；常规跳过无交互；旧 check 不改变退出语义。
- [ ] init/generate/update --lang en|zh，默认 en；默认建议不作为仓库指令。
- [ ] setup、命令、依赖、树使用仓库证据；suggested 留 doctor 建议区。
- [ ] 英文模板和完整中文模板；已有手写内容及 header 不翻译。
- [ ] 拆分默认单文件与显式六类安装冒烟；版本 0.2.0、CHANGELOG。
- [ ] Specification review -> 修复 -> quality review -> 修复 -> 本地阶段提交。

## Task 4 — v0.3.0 预览、写入与漂移

- [ ] 纯候选内容计算与磁盘写入分离，同一 FileChange 用于 dry-run/check/write。
- [ ] dry-run 无目录、临时文件或 mtime 变化；--diff 显式显示文本，MCP 仅字段路径。
- [ ] 无变化不写；写前重读快照；同目录临时文件原子替换，清理自身临时文件。
- [ ] 保持 BOM、EOL、frontmatter、手写前后缀；错误文件不写，独立文件继续处理。
- [ ] 不宣称跨文件事务或跨进程锁；输入改变后两次命令独立重算。
- [ ] update --check 只比较受管正文；MCP 用户服务定义不适用漂移判定。
- [ ] 无可比较内容失败；手写变化无漂移；声明变化产生漂移。
- [ ] 排除生成文件的目录树自引用，固定顺序，不加入时间戳或本机环境。
- [ ] 独立 changes schema，JSON stdout 和退出码回归；版本 0.3.0、CHANGELOG。
- [ ] Specification review -> 修复 -> quality review -> 修复 -> 本地阶段提交。

## Task 5 — 文档、演示、发布准备

- [ ] 英文 README、完整 README.zh-CN.md：定位、只读入口、真实样例、保护规则、支持矩阵、升级与故障说明。
- [ ] Python/TypeScript/Go 可复制样例；记录固定输入的真实输出，短终端演示，不含个人环境。
- [ ] 手动迁移指南、命令来源说明、CI 示例、贡献指南、具体 issue 模板。
- [ ] 支持表区分格式测试和客户端实测，未测明确写未验证。
- [ ] 开发依赖补 Ruff，干净环境能运行 README 开发步骤。
- [ ] 标签/源码/包版本一致门禁；同提交构建 wheel/sdist 和校验值，供人工发布。
- [ ] 不自动执行 PyPI/GitHub Release/标签/topics 更新；保留准确的发布清单。
- [ ] 不伪造客户端加载、用户试点、star 增长或发布结果；5–8 人试点作为后续人类活动。
- [ ] 最终 spec/quality review；全量测试、Ruff、Python3.10/3.13 隔离安装及 CLI 冒烟。
- [ ] 交付改动、验证结果、未测范围和必要风险；提交/推送遵循已有用户授权，公开发布另需授权。

## 非本轮范围

项目配置持久化、Monorepo 自动继承、更多目标、完整同步、源码打包器、托管网页、MCP 安装器、规则商店、完整需求管理平台。用户试点、真实客户端测试和外部发布需要实际环境，不用单元测试冒充。

## 执行记录

- 2026-10-26：隔离 worktree codex/repoize-roadmap 建立；基线 139 tests passed，Ruff check/format 通过。
