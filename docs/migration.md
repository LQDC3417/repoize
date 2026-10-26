# Upgrading Repoize

[中文](migration.zh-CN.md)

Repoize does not move, delete, or merge legacy configuration files automatically. Back up the complete original file before changing paths. An explicit `--force` replaces a current target; it is not permission to migrate or remove another file.

## v0.1.2: current configuration formats

| Configuration | Legacy output | Current output |
| --- | --- | --- |
| Claude project MCP | `.claude/mcp.json` | `.mcp.json` |
| Cursor project rule | `.cursorrules` | `.cursor/rules/repoize.mdc` |
| Claude project skill | `.claude/skills/project-dev/SKILL.md` with a generated wrapper before YAML | Same path, YAML at the beginning |

When only a legacy path exists, generation/update stops for that type and leaves the file intact. Other independent types can still finish. A modern MCP file is not merged with a legacy MCP file. Cursor legacy/current coexistence requires manual resolution before Repoize writes its rule.

### Claude MCP

1. Keep an exact backup of `.claude/mcp.json` outside active MCP configuration paths.
2. If `.mcp.json` does not exist, copy the complete JSON document there, including all custom servers and unknown keys.
3. If `.mcp.json` already exists, compare the two documents yourself. Keep each server definition as a whole; do not combine one server's command with another definition's arguments.
4. Confirm that the destination is a JSON object with an object-valued `mcpServers` entry. Keep credentials private and use supported environment references where appropriate.
5. Review machine-specific paths and external runtime requirements. Repoize does not install or start the configured servers.
6. Keep or archive the legacy file as your team requires. Repoize only updates the current path and reports the remaining legacy file.

New MCP generation produces `{"mcpServers": {}}`. It is a configuration scaffold, not a working server setup. `generate --type mcp --force` replaces the entire destination, including existing server definitions.

Force does not bypass invalid JSON, damaged managed markers, legacy migration checks, or path protections. Repair or restore a damaged file deliberately before regenerating it.

See [Claude project scope](https://code.claude.com/docs/en/mcp#project-scope). Client approval and actual server connection are separate from JSON validation.

### Cursor

1. Back up `.cursorrules` and any existing `.cursor/rules` files.
2. If `repoize.mdc` already exists, compare and resolve the content manually; do not overwrite it blindly.
3. Create `.cursor/rules/repoize.mdc`, beginning with:

   ```yaml
   ---
   description: Project development context maintained with Repoize
   alwaysApply: true
   ---
   ```

4. Put the complete old rule body after this frontmatter. Preserve handwritten content and a valid generated-marker pair if present.
5. Move the old `.cursorrules` out of its active name, for example to a separately reviewed backup. Do not leave both copies active.
6. Verify the rule in the Cursor version you use, then run an ordinary Repoize update if the body has managed markers.

Existing frontmatter is user-owned: Repoize validates it and preserves its original text. Files without managed markers remain handwritten files and are skipped by ordinary updates.

See [Cursor project rules](https://cursor.com/docs/rules).

### Skill frontmatter

1. Back up `.claude/skills/project-dev/SKILL.md`.
2. Move the existing YAML metadata to the first lines of the file, before HTML comments. If there is a handwritten preface, decide where it belongs in the Markdown body; do not discard it.
3. Set `name: project-dev` to match the containing directory. Keep a non-empty description explaining when to use the skill.
4. Keep exactly one generated-marker pair around the generated Markdown body, after the YAML block.
5. Remove an automatically inserted license claim if it was never authorized for your project; preserve any deliberately authored licensing information.
6. Keep handwritten content outside the managed body and verify discovery in your client.

The intended structure is:

```markdown
---
name: project-dev
description: Development context for this project; use when working in this repository.
---

<!-- repoize:generated-start -->
Generated Markdown body
<!-- repoize:generated-end -->

Handwritten notes remain outside the generated region.
```

See the [Agent Skills specification](https://agentskills.io/specification). Correct format does not prove that a client loaded or used the skill.

## v0.2.0: smaller defaults and explicit language

- `init` creates only `AGENTS.md`; `init --type claude` adds the Claude file.
- `generate --type ...` generates exactly the requested types. `cursor` is preferred; `cursorrules` remains an alias.
- MCP and Skill are opt-in types. No command silently installs MCP services.
- `update` only updates existing files at Repoize's fixed generated paths; it does not adopt arbitrary custom rules. Use `generate` to create a missing target.
- Generated content defaults to English. Use `--lang zh` for Chinese on both generation and later updates; no project preference file is saved.
- Handwritten sections and existing frontmatter are not translated.
- Default commands do not inspect local environment variables. `analyze --include-env` explicitly adds platform/tool-version information only. `--no-env` is still accepted.
- `doctor` reports concrete findings. The old `check` remains a compatibility report, not a CI gate.

The analysis JSON v1 shape is preserved. Doctor uses its own report/schema. An analysis report still contains project paths and should be reviewed before sharing.

## v0.3.0: preview and drift checks

Use `--dry-run` before writing and add `--diff` only when you want to inspect existing file text locally. MCP previews report field paths rather than secret values. A preview is not a saved transaction: a later command reads and calculates from the repository again.

`update --check` compares managed content without writing. Handwritten notes do not count as drift. User-owned MCP server definitions are outside its drift comparison; use `doctor --type mcp` for supported structure checks. A repository without comparable managed content cannot pass the drift check.

For Chinese output, use the same `--lang zh` in local updates and CI. See the installed command's `--help` for report formats and exit statuses.
