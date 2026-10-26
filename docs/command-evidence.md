# Where project commands come from

[中文](command-evidence.zh-CN.md)

Repoize reads supported manifests and configuration files. It never runs the commands it discovers. A declaration can still refer to a missing executable, broken script, or unavailable service.

| Source kind | Meaning | Generated instructions |
| --- | --- | --- |
| `declared` | A project declaration supplies the command or named entry | Included |
| `inferred` | A supported local configuration supplies evidence for a conventional command | Included, with source |
| `suggested` | A profile or adapter supplies a general suggestion without sufficient project evidence | Excluded; doctor explains the source, while legacy analysis can retain the command string |

Every command has `verification: "not_run"`. No command receives a confidence percentage or a passing-test claim. Repeated evidence is deduplicated; one command can have several source locations.

## Examples of evidence

- A `package.json` test script produces a package-runner command, with `scripts.test` as a source selector. The command does not prove the script's tool is installed.
- An explicit `packageManager` selects the JavaScript runner when evidence does not conflict. Otherwise a unique supported lockfile supplies evidence. Conflicting lockfiles or a declaration/lockfile mismatch produce a warning and no runner choice. With neither declaration nor lockfile, the adapter uses its npm default.
- A Python project declaration supports its installation command. The `.[dev]` extra is used only when that extra is declared. Test/tool configuration and actual dependency declarations can support additional commands.
- A supported Go, Cargo, Maven, Gradle, Composer, or other manifest can supply conventional build/test commands. Coverage depends on the adapter; Repoize does not understand every build system.
- A source-file extension alone does not prove that pytest, Ruff, or a development extra exists. Generic profile suggestions stay out of generated instructions.

Inspect the actual result for your repository:

```bash
repoize doctor /path/to/project
repoize doctor /path/to/project --format json
```

Command sources contain a kind, a relative path when available, and a selector. Selectors describe a configuration location, not a copy of its raw value. Doctor reports syntax/structure problems separately and does not echo malformed source lines.

## Diagnostic rules

| Rule | What to inspect |
| --- | --- |
| `CFG001` | No discovered configuration, or a required selected type is missing |
| `CFG002` | A known legacy configuration entry |
| `CFG003` | File readability, UTF-8, emptiness, or unsafe links |
| `CFG004` | Supported JSON/YAML syntax and object structure |
| `CFG005` | Skill metadata and directory/name agreement |
| `CFG006` | Cursor frontmatter and supported field types |
| `CFG007` | Empty MCP setup or empty server entry |
| `UPD001` | Managed-marker integrity or frontmatter overlap |
| `SRC001` | A command source could not be parsed as a supported declaration |
| `CMD001` | A command has only general suggestions |
| `CMD002` | Conflicting package-runner evidence |

Use each finding's severity, evidence, and suggested fix. Rule IDs identify the problem category; they are not a code-quality score. See [CI exit statuses](ci.md) and [support boundaries](support.md).

## JSON compatibility

`analyze --format json` keeps analysis schema v1, including its five arrays of command strings. This compatibility report does not carry the new evidence model. `validate` validates that analysis report only.

Doctor has its own versioned [schema](../src/repoize/schemas/doctor.schema.json). Change previews use a separate [changes schema](../src/repoize/schemas/changes.schema.json). Do not feed either report to the old analysis validator or infer that a valid report means commands executed successfully.
