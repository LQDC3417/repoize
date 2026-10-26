# Supported configurations

[中文](support.zh-CN.md)

Repoize checks known file paths and supported structure. File discovery, format validation, client discovery, and model behavior are different results. A passed format test does not mean an AI client loaded or obeyed the content.

| Type | Current generated path | Legacy path | Supported structure checks | Actual client loading |
| --- | --- | --- | --- | --- |
| `agents` | `AGENTS.md` | — | Readable, non-empty Markdown; managed-marker integrity | Not verified |
| `claude` | `CLAUDE.md` | — | Readable, non-empty Markdown; managed-marker integrity | Not verified |
| `cursor` (`cursorrules` alias) | `.cursor/rules/repoize.mdc` | `.cursorrules` | MDC frontmatter and body; managed-marker integrity | Not verified |
| `copilot` | `.github/copilot-instructions.md` | — | Readable, non-empty Markdown; managed-marker integrity | Not verified |
| `mcp` | `.mcp.json` | `.claude/mcp.json` | JSON object and supported `mcpServers` structure | Not verified; server connection is separate |
| `skill` | `.claude/skills/project-dev/SKILL.md` | Old wrapper at the same path | Leading YAML; required metadata, directory/name match; managed-marker integrity | Not verified |

Doctor also discovers existing MDC rules under `.cursor/rules` and existing skills in the supported Claude project skill directory. It does not claim to implement every client's complete parser or every scope. Nested AGENTS inheritance, global configurations, external symlink targets, and Monorepo inheritance are outside this release's validation.

Generated Markdown has a Repoize-managed body. Frontmatter and text outside the markers remain user-owned. An otherwise valid handwritten file does not need Repoize markers to be usable; it is simply not updated by Repoize.

An empty MCP server object is a valid scaffold, not a configured or connected server. An unknown field is not automatically invalid. Structural validation does not execute a server, resolve credentials, or prove network connectivity.

## Standards reviewed

Reviewed on 2026-10-26:

- [Claude project MCP scope](https://code.claude.com/docs/en/mcp#project-scope)
- [Cursor rules](https://cursor.com/docs/rules)
- [Agent Skills specification](https://agentskills.io/specification)

The implementation's automated checks are verified with the repository tests and installed-package smoke checks. Actual client loading has not been verified for this roadmap. To contribute a client result, report client version, operating system, date, a minimal public fixture, discovery result, and warnings. Do not include private repository instructions or credentials.

See [manual migration](migration.md) for legacy paths.
