# Repoize 升级与手动迁移

[English](migration.md)

Repoize 不自动移动、删除或合并旧配置。改路径前保留原文件的完整副本。`--force` 只表示覆盖当前目标文件，不代表迁移、删除其他文件。

## v0.1.2：当前配置格式

| 配置 | 旧输出 | 当前输出 |
| --- | --- | --- |
| Claude 项目 MCP | `.claude/mcp.json` | `.mcp.json` |
| Cursor 项目规则 | `.cursorrules` | `.cursor/rules/repoize.mdc` |
| Claude 项目 Skill | 同一路径，但 HTML 标记位于 YAML 前 | `.claude/skills/project-dev/SKILL.md`，YAML 位于首部 |

仅旧路径存在时，该类型停止生成或更新，文件保留；其他独立类型继续处理。新旧 MCP 不自动合并；Cursor 新旧规则并存时，先手动处理重复规则，再让 Repoize 写入。

### Claude MCP

1. 在非生效配置路径保留 `.claude/mcp.json` 的完整备份。
2. 若根目录没有 `.mcp.json`，完整复制旧 JSON，包括自定义服务器和未知字段。
3. 若新文件已存在，手动比较。服务器定义作为整体处理，不能把一份定义的 command 与另一份的 args 混用。
4. 确认根结构为 JSON 对象，`mcpServers` 也是对象。凭据保持私密，按客户端支持方式使用环境变量引用。
5. 检查本机路径和外部运行时要求。Repoize 不安装或启动服务。
6. 按团队需要保留或归档旧文件；Repoize 只更新新路径，并提示旧文件仍存在。

新生成内容为 `{"mcpServers": {}}`，只代表合法空模板，不代表已有可用服务。`generate --type mcp --force` 会替换整个文件，包括原有服务器定义。

Force 不绕过无效 JSON、损坏受管标记、旧格式迁移检查和路径保护。损坏文件需先明确修复或恢复，再重新生成。

依据：[Claude 项目作用域](https://code.claude.com/docs/en/mcp#project-scope)。客户端批准和服务连接需要单独验证。

### Cursor

1. 备份 `.cursorrules` 和已有 `.cursor/rules` 文件。
2. 若 `repoize.mdc` 已存在，先手动比较，避免覆盖已有规则。
3. 新文件 `.cursor/rules/repoize.mdc` 首部使用：

   ```yaml
   ---
   description: Project development context maintained with Repoize
   alwaysApply: true
   ---
   ```

4. 在 YAML 后保留旧规则的完整正文、手写内容和合法受管标记。
5. 确认新文件后，将旧 `.cursorrules` 移出原生效名称，作为备份保留；不要保留两份同时生效的规则。
6. 在实际使用的 Cursor 版本确认规则被发现，再对有受管标记的正文运行普通更新。

已有 frontmatter 归用户维护：Repoize 校验并保留其原文。无受管标记的文件仍为手写配置，普通更新跳过。

依据：[Cursor 项目规则](https://cursor.com/docs/rules)。

### Skill 首部

1. 备份 `.claude/skills/project-dev/SKILL.md`。
2. 将 YAML 元数据放在文件最前面、HTML 注释之前。若有手写前言，明确放入 Markdown 正文，不能丢弃。
3. 将 name 改为与目录一致的 `project-dev`，description 保持非空并说明使用场景。
4. YAML 之后的生成正文只保留一对受管标记。
5. 未经项目授权的自动 license 声明应去除；主动编写的授权说明保留。
6. 手写说明放在受管正文之外，再验证客户端发现情况。

结构示例：

```markdown
---
name: project-dev
description: 本项目开发上下文，在维护此仓库时使用。
---

<!-- repoize:generated-start -->
生成的 Markdown 正文
<!-- repoize:generated-end -->

手写说明放在生成区间外。
```

依据：[Agent Skills 规范](https://agentskills.io/specification)。格式正确不能证明客户端已加载或采用。

## v0.2.0：最小默认与语言选项

- `init` 默认只生成 `AGENTS.md`；`init --type claude` 增加 Claude 配置。
- `generate --type ...` 只生成所选类型；推荐 `cursor`，保留 `cursorrules` 别名。
- MCP、Skill 显式选择；不自动安装服务。
- `update` 只更新 Repoize 固定生成路径中的已有文件，不认领任意自定义规则；缺失目标使用 `generate` 创建。
- 生成默认英文；中文生成与后续更新均传入 `--lang zh`，不保存隐藏的项目偏好文件。
- 手写区和已有 frontmatter 不自动翻译。
- 默认不扫描本机环境。`analyze --include-env` 仅显式增加平台与工具版本；`--no-env` 保持可用。
- `doctor` 给具体诊断；旧 `check` 保留兼容报告语义，不作为 CI 阻断入口。

分析 JSON v1 结构保留，doctor 使用独立报告和 Schema。分析报告仍含项目路径，分享前需要检查。

## v0.3.0：预览和漂移检查

写入前可使用 `--dry-run`；仅在本地需要阅读旧文件文本时增加 `--diff`。MCP 预览只列字段路径，不展示秘密值。预览不保存事务；后续命令重新读取仓库并计算。

`update --check` 只读比较受管正文；手写说明不构成漂移。用户维护的 MCP 服务定义不属于漂移比较范围，其结构可用 `doctor --type mcp` 检查。没有可比较受管内容的项目不能通过漂移检查。

中文项目本地更新和 CI 使用一致的 `--lang zh`。具体报告格式与退出状态以已安装版本的 `--help` 为准。
