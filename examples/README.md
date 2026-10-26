# Reproduce a local workflow

[中文](README.zh-CN.md) · [Actual terminal record](demo.txt) · [Verification scope](verification.md)

These examples require the **0.3.0 development source**, not the published 0.1.0 package. From a source checkout, install into your virtual environment with `python -m pip install -e ".[dev]"`.

## 1. Copy a fixture

Run from the Repoize checkout root. This creates a sibling demo directory; copying fails if the destination already exists, so it cannot overwrite an earlier experiment.

```bash
python -c "import shutil; shutil.copytree('tests/fixtures/languages/python', '../repoize-demo/python-fixture', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))"
repoize --version
repoize analyze ../repoize-demo/python-fixture
repoize init ../repoize-demo/python-fixture --dry-run
repoize init ../repoize-demo/python-fixture
repoize doctor ../repoize-demo/python-fixture --type agents
repoize update ../repoize-demo/python-fixture --check --type agents
```

All commands above should return 0. Generation creates only `AGENTS.md`. For Chinese output, add `--lang zh` to `init` and every later `update`.

## 2. Keep a handwritten note through an update

Open the demo's `AGENTS.md`. Above the first `<!-- repoize:generated-start -->`, add a team note. In the copied `pyproject.toml`, rename `greet = "app:main"` to `hello = "app:main"`.

```bash
repoize update ../repoize-demo/python-fixture --check --type agents
repoize update ../repoize-demo/python-fixture --dry-run --diff --type agents
repoize update ../repoize-demo/python-fixture --type agents
repoize update ../repoize-demo/python-fixture --check --type agents
```

The first check returns **1** for drift. The preview, update, and final check return **0**. Review the changed command source and confirm that your note survives. Handwritten changes alone do not count as drift.

## 3. Inspect the recorded output

- [Initial English AGENTS.md](generated/python/AGENTS.en.md)
- [Initial Chinese AGENTS.md](generated/python/AGENTS.zh.md)
- [Updated English file with the handwritten note](generated/python/AGENTS.updated.en.md)
- [Actual terminal output](demo.txt), recorded on 2026-10-26 with Repoize 0.3.0 on Windows/Python 3.13.12. The temporary working-directory path is replaced with `<demo>`; prompts, edit captions, and exit-status annotations are added. Trailing whitespace is stripped for storage. Output text is otherwise preserved. The terminal analysis report retains its current Chinese interface even when generated content defaults to English.

The [Python](../tests/fixtures/languages/python), [TypeScript](../tests/fixtures/languages/typescript), and [Go](../tests/fixtures/languages/go) fixtures are inputs for Repoize's evidence extraction. To try another, copy its directory and pass that copy to the same commands. The TypeScript manifest intentionally supplies script evidence without proving all script tools are installed. Do not treat these fixtures as verified complete applications.

Only the Python sample's `python app.py` and `python -m pytest` were explicitly executed as fixture verification. Repoize did not run any discovered project command; TypeScript/Go build and test commands were not executed. A format check does not establish client discovery or model compliance.

The Repoize repository itself retains historical manually maintained configuration files; this demo does not migrate or overwrite them. See [migration](../docs/migration.md), [support](../docs/support.md), and the separate [MCP scaffold example](mcp/README.md).
