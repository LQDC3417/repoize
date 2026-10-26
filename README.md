# Repoize

**Repository facts for AI coding tools.**

Generate `AGENTS.md` and selected tool configurations from repository evidence. Inspect problems and command sources, preview updates, and preserve handwritten instructions.

[中文](README.zh-CN.md) · [Examples](examples/README.md) · [Support](docs/support.md) · [Migration](docs/migration.md) · [Contributing](CONTRIBUTING.md)

[![PyPI](https://img.shields.io/pypi/v/repoize.svg)](https://pypi.org/project/repoize/)
[![Python](https://img.shields.io/pypi/pyversions/repoize.svg)](https://pypi.org/project/repoize/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> This README describes the **0.3.0 development source**. The published PyPI package was still **0.1.0** when checked on 2026-10-26 and does not contain the new commands below. Use source installation to try this roadmap; check the [releases](https://github.com/LQDC3417/repoize/releases) before choosing a package version.

## Try it on an existing repository

Requires Python 3.10+ and Git for source installation. Use a Python virtual environment or an isolated tool installer.

```bash
python -m pip install "git+https://github.com/LQDC3417/repoize.git"

# Read-only: inspect configurations and command evidence.
repoize doctor /path/to/project

# Read-only: review the planned default output.
repoize init /path/to/project --dry-run

# Create AGENTS.md; existing files are skipped.
repoize init /path/to/project
```

With [uv](https://docs.astral.sh/uv/) already installed, run the source without a permanent tool installation:

```bash
uvx --from "git+https://github.com/LQDC3417/repoize.git" repoize doctor /path/to/project
```

For the published stable package, use `python -m pip install repoize` and consult that version's `--help`; available commands may differ.

## What you get

- **Evidence before instructions.** Commands distinguish declarations, configuration-based inference, and generic suggestions. Extraction does not mean execution or success.
- **Specific diagnostics.** Findings identify a rule, file, evidence, and next step. A Cursor-only repository does not need Claude, MCP, or Skill files to pass its selected checks.
- **Reviewable maintenance.** Preview the same candidate content used for writing. Normal updates preserve handwritten text and existing frontmatter; unchanged files are not rewritten.
- **Small defaults.** `init` creates `AGENTS.md`. MCP and Skill are opt-in. Default operations do not scan local environment variables, run project scripts, upload code, or call an LLM.

See the [recorded local workflow](examples/README.md) for real generated English/Chinese files and an update that keeps a handwritten note.

## Select the output

```bash
# AGENTS.md plus Claude instructions.
repoize init /path/to/project --type claude

# Exactly the selected types.
repoize generate /path/to/project --type cursor --type copilot

# Chinese content; use the same language on later updates.
repoize init /path/to/project --lang zh

# Optional MCP scaffold and project Skill.
repoize generate /path/to/project --type mcp --type skill
```

| Type | Generated path |
| --- | --- |
| `agents` | `AGENTS.md` |
| `claude` | `CLAUDE.md` |
| `cursor` | `.cursor/rules/repoize.mdc` |
| `copilot` | `.github/copilot-instructions.md` |
| `mcp` | `.mcp.json` |
| `skill` | `.claude/skills/project-dev/SKILL.md` |

`cursorrules` remains an alias for `cursor`. Legacy paths are detected, not moved automatically. Read [manual migration](docs/migration.md) before changing an existing setup.

MCP generation creates an empty `mcpServers` object. It does not choose, install, or start servers. An empty scaffold is reported as not yet configured. See the [MCP example](examples/mcp/README.md) before adding a server yourself.

## Inspect and update

```bash
repoize doctor /path/to/project --type cursor --strict
repoize doctor /path/to/project --format json
repoize update /path/to/project --dry-run
repoize update /path/to/project --dry-run --diff
repoize update /path/to/project
repoize update /path/to/project --check
```

Normal updates affect existing files at the generated paths listed above, not missing targets or arbitrary custom rules. Doctor can inspect additional supported rule/skill files without making them Repoize-owned. Text outside Repoize's markers and existing frontmatter remain user-owned. Invalid files, broken markers, legacy conflicts, and unsafe paths are reported rather than silently overwritten.

`--force` on generation replaces the entire valid current target, including handwritten content or MCP server definitions. Preview that replacement with `--force --dry-run`. Force does not bypass migration and path protections.

Text diffs are explicit because existing files can contain private content. MCP previews show field paths rather than secret values. A later command recalculates its preview; it is not a saved approval transaction.

Drift checks compare managed text, not handwritten edits or user-owned MCP definitions. No comparable managed content means the check cannot pass. See the [CI example](docs/ci.md) for language selection and exit statuses.

## Analysis and JSON

```bash
repoize analyze /path/to/project
repoize analyze /path/to/project --format json --output analysis.json
repoize validate analysis.json
# Explicit platform/tool versions; no environment variable values.
repoize analyze /path/to/project --include-env
```

Analysis JSON v1 remains compatible with `validate`. Doctor and change reports have separate schemas. JSON stdout contains data only; status messages go to stderr. Analysis reports still include project paths: review before sharing.

See [command evidence and diagnostic rules](docs/command-evidence.md) for source kinds, extraction limits, and rule IDs.

`check` remains the older coverage report, not a CI gate. Scores reflect detected setup, not code correctness, client loading, or model compliance. Use `doctor` for concrete findings and `update --check` for drift.

## When Repoize fits

Use Repoize to extract an existing repository's development facts and maintain generated context as the repository changes.

For distributing already-authored shared rules, also consider [Rulesync](https://github.com/dyoshikawa/rulesync) and [Ruler](https://github.com/intellectronica/ruler). For packing source code into an LLM context, see [Repomix](https://github.com/yamadashy/repomix) and [Gitingest](https://github.com/coderamp-labs/gitingest). These workflows can complement Repoize.

Profiles cover Python, JavaScript, TypeScript, Go, Rust, Java, Ruby, and PHP, not every build system or framework. [Support details](docs/support.md) distinguish format checks from actual client tests.

## Development and feedback

```bash
git clone https://github.com/LQDC3417/repoize.git
cd repoize
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src/ tests/ scripts/
python -m ruff format --check src/ tests/ scripts/
```

Useful contributions: a minimal misidentified manifest, a command-source regression, or a client-discovery record. Use a small public/redacted fixture; do not upload tokens or proprietary instructions. See [contributing](CONTRIBUTING.md), [the roadmap](docs/superpowers/plans/2026-10-26-repoize-roadmap.md), and [release preparation](docs/releasing.md).

MIT license. See [LICENSE](LICENSE).
