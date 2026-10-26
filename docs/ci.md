# Check managed context in CI

[中文](ci.zh-CN.md)

This example uses the development source because the published 0.1.0 package does not contain `update --check`. After a public release, install the exact verified package version instead. For reproducible source installs, replace `main` with the full Repoize commit you have reviewed.

First generate and review `AGENTS.md`, then commit it to your own repository. CI checks existing managed content; it does not initialize a project or commit updates.

```yaml
name: Repoize context
on: [push, pull_request]
permissions:
  contents: read
jobs:
  context:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install development Repoize
        run: python -m pip install "git+https://github.com/LQDC3417/repoize.git@main"
      - name: Check supported structure
        run: repoize doctor --type agents
      - name: Check managed content
        run: repoize update --check --type agents
```

For Chinese generated content, change the last command to `repoize update --check --type agents --lang zh`. Use the same generation language locally and in CI. To check another existing generated type, specify it explicitly; do not require every tool's files in a single-tool project.

## Exit statuses

| Command | 0 | 1 | 2 | 3 |
| --- | --- | --- | --- | --- |
| `doctor` | No error findings | Errors; also warnings with `--strict` | Invalid arguments/path | Cannot complete diagnostics |
| `update --check` | Comparable managed content is current | Drift or a content conflict | Invalid arguments/path | Invalid files, runtime failure, or no comparable content |

Warnings do not fail doctor unless `--strict` is used. No discovered configuration produces an explicit warning rather than a claim that all configurations passed. Use an explicit type to require its entry file.

`check` is the older coverage report and does not supply these gate semantics. `validate` only validates analysis JSON v1, not doctor/change reports.

## What drift means

- Only managed generated text is compared; handwritten sections do not trigger drift.
- Repository changes can alter inferred commands and generated context.
- MCP server definitions are user-owned and outside managed-text drift checks; use doctor for supported MCP structure checks.
- A repository without comparable managed content cannot pass the drift gate.
- Generated output paths are excluded from the generated directory tree to avoid a first-generation self-reference diff.

CI never writes a fix. Reproduce locally with `repoize update --dry-run --diff`, review the result, run `repoize update`, and commit the reviewed configuration yourself.

Existing text diffs may include private repository instructions. Inspect them locally before sharing logs. MCP reports do not print server secret values. See [support boundaries](support.md) and [migration](migration.md).
