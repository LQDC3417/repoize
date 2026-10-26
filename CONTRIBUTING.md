# Contributing

[中文](CONTRIBUTING.zh-CN.md)

Useful small contributions include a minimal misidentified manifest, a command-source regression, a configuration-format fixture, or a documented client-discovery result.

## Development

Use Python 3.10 or newer in a virtual environment, then install the project and development tools:

```bash
git clone https://github.com/LQDC3417/repoize.git
cd repoize
python -m venv .venv
```

Activate `.venv` using `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on Linux/macOS, then run:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check src/ tests/ scripts/
python -m ruff format --check src/ tests/ scripts/
```

For a coverage report, run `python -m pytest --cov=src/repoize --cov-report=term-missing`. Work on a focused branch, use descriptive `feat:`, `fix:`, `docs:`, or `test:` commits, and open a pull request for review.

Keep changes focused. Follow the existing style: Chinese comments/docstrings, English identifiers, and straightforward functions. Add a regression that fails for the reported behavior before fixing it. Changes to CLI behavior also need exit-status and stdout/stderr checks.

## Safety and compatibility

- Do not execute a scanned repository's scripts to identify commands.
- Keep handwritten text, existing frontmatter, and user-owned MCP definitions intact.
- Preserve analysis JSON v1. New report shapes need their own schema and tests.
- Use synthetic credentials in privacy tests, never real environment dumps.
- Preview tests must prove that files, directories, and modification times did not change.
- Update English and Chinese documentation together when public behavior changes.
- A format assertion is not a client-loading test. Record actual client version and observations separately.

## Reproductions

Open a focused issue with Repoize version, operating system, the command, expected/actual behavior, and a small public or redacted fixture. Do not include tokens, server environment values, private URLs, proprietary instructions, or a full private repository.

If reporting an unexpected file modification, keep an original copy locally. Describe what changed; do not overwrite your only reproduction while testing a fix.

## Client validation

The [support matrix](docs/support.md) distinguishes format checks from actual loading. A useful client record contains the exact version, operating system, date, minimal safe input, whether the file was discovered, and any warnings. Do not claim that a successful discovery guarantees model compliance.

## Pull requests

Describe the concrete problem, resulting behavior, relevant tests, and remaining limits. Avoid unrelated refactors. A parser or target addition needs a real fixture and an explanation of which syntax/scope it supports.

Package publishing and repository metadata changes are separate maintainer actions. Do not add automatic network access, telemetry, MCP installation, or release side effects to ordinary analysis and generation.

## Participation and license

Respect other participants, accept constructive criticism, and keep discussion focused on the project. Contributions are provided under the project's [MIT license](LICENSE).

## Build and release checks

Use the [release instructions](docs/releasing.md) to build and check one wheel/sdist batch. `python scripts/check_release.py` checks source versions without importing the package; `--tag v0.3.0` also checks the intended tag. Nothing in the checker publishes a package. Run the [local fixture workflow](examples/README.md) when changing generated output.
