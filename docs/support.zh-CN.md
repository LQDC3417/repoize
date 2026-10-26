# 配置支持范围

[English](support.md)

Repoize 检查已知路径和已支持的结构。文件被发现、格式校验通过、客户端加载成功、模型遵守指令是不同结果；格式测试通过不能代替客户端验证。

| 类型 | 当前生成路径 | 旧路径 | 支持的结构检查 | 实际客户端加载 |
| --- | --- | --- | --- | --- |
| `agents` | `AGENTS.md` | — | 可读、非空 Markdown；受管标记完整性 | 未验证 |
| `claude` | `CLAUDE.md` | — | 可读、非空 Markdown；受管标记完整性 | 未验证 |
| `cursor`（别名 `cursorrules`） | `.cursor/rules/repoize.mdc` | `.cursorrules` | MDC 首部与正文；受管标记完整性 | 未验证 |
| `copilot` | `.github/copilot-instructions.md` | — | 可读、非空 Markdown；受管标记完整性 | 未验证 |
| `mcp` | `.mcp.json` | `.claude/mcp.json` | JSON 对象及已支持的 mcpServers 结构 | 未验证；服务连接需单独确认 |
| `skill` | `.claude/skills/project-dev/SKILL.md` | 同路径的旧包装结构 | 首部 YAML、必填元数据、目录与名称匹配、标记完整性 | 未验证 |

Doctor 也发现 `.cursor/rules` 下已有 MDC 和支持的 Claude 项目 Skill 目录内已有 Skill；不宣称复刻客户端完整解析器或覆盖全部作用域。本版不验证嵌套 AGENTS 继承、全局配置、项目外链接目标和 Monorepo 继承。

Repoize 管理 Markdown 的生成正文。frontmatter 和标记区间外文字归用户维护。合法手写配置无需 Repoize 标记，也可以由客户端使用；只是 Repoize 不更新它。

空 MCP 服务器对象是合法模板，不代表服务已配置或连接。未知字段不自动视为错误。结构检查不启动服务器、不解析凭据、不验证网络连接。

## 规范核对

核对日期：2026-10-26。

- [Claude 项目 MCP 作用域](https://code.claude.com/docs/en/mcp#project-scope)
- [Cursor 规则](https://cursor.com/docs/rules)
- [Agent Skills 规范](https://agentskills.io/specification)

自动化结构检查通过仓库测试及安装包冒烟核验；本轮未进行真实客户端加载验收。贡献客户端记录时，请包含版本、操作系统、日期、最小公开样例、是否发现和警告信息，不提供私有指令或凭据。

旧格式参见[手动迁移](migration.zh-CN.md)。
