import json
from pathlib import Path

import pytest

from repoize.analyzer.cmd_extractor import extract_commands
from repoize.analyzer.language_profiles import get_language_profile


def test_defaults_are_not_generation_evidence(tmp_path):
    (tmp_path / "demo.py").write_text("pass", encoding="utf-8")
    commands = extract_commands(tmp_path, get_language_profile("Python"))
    assert commands.test == ["pytest"]
    assert commands.generation_dict() == dict.fromkeys(("setup", "build", "test", "lint", "format", "run"), [])
    assert all(item["verification"] == "not_run" for item in commands.evidence_dict())
    assert all(source["kind"] == "suggested" for item in commands.evidence_dict() for source in item["sources"])
    assert set(commands.to_dict()) == {"build", "test", "lint", "format", "run"}
    assert commands.setup == []


def test_pyproject_multiple_sources_and_setup(tmp_path):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text(
        '[project]\nname="demo"\ndependencies=["pytest", "ruff"]\n'
        '[project.optional-dependencies]\ndev=["pytest"]\n[tool.pytest]\n[tool.ruff]\n',
        encoding="utf-8",
    )
    commands = extract_commands(tmp_path)
    assert commands.test == ["pytest"]
    evidence = next(item for item in commands.evidence_dict() if item["command"] == "pytest")
    assert {source["selector"] for source in evidence["sources"]} == {
        "project.dependencies",
        "project.optional-dependencies.dev",
        "tool.pytest",
    }
    assert commands.generation_dict()["setup"] == ['pip install -e ".[dev]"']
    assert commands.generation_dict()["lint"] == ["ruff check ."]
    manifest.write_text('[project]\nname="demo"', encoding="utf-8")
    assert extract_commands(tmp_path).generation_dict()["setup"] == ["pip install -e ."]
    manifest.write_text("[tool.ruff]\n", encoding="utf-8")
    assert extract_commands(tmp_path).generation_dict()["setup"] == []
    (tmp_path / "requirements-dev.txt").write_text("pytest", encoding="utf-8")
    assert extract_commands(tmp_path).generation_dict()["setup"] == ["pip install -r requirements-dev.txt"]


@pytest.mark.parametrize("runner,lock", [("pnpm", "pnpm-lock.yaml"), ("yarn", "yarn.lock"), ("bun", "bun.lock")])
def test_javascript_runner_evidence(tmp_path, runner, lock):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "test"}}), encoding="utf-8")
    (tmp_path / lock).write_text("", encoding="utf-8")
    commands = extract_commands(tmp_path, get_language_profile("JavaScript"))
    assert commands.test == [f"{runner} run test"]
    evidence = next(item for item in commands.evidence_dict() if item["category"] == "test")
    assert {item["path"] for item in evidence["sources"]} == {"package.json", lock}
    assert commands.generation_dict()["setup"] == [f"{runner} install"]


def test_runner_conflicts_do_not_guess(tmp_path):
    manifest = tmp_path / "package.json"
    manifest.write_text('{"packageManager":"pnpm@10","scripts":{"test":"test"}}', encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    commands = extract_commands(tmp_path, get_language_profile("JavaScript"))
    assert commands.generation_dict()["test"] == []
    assert commands.generation_dict()["setup"] == []
    assert any(issue["rule_id"] == "CMD002" for issue in commands.issues)
    (tmp_path / "package-lock.json").unlink()
    assert extract_commands(tmp_path).test == ["pnpm run test"]


@pytest.mark.parametrize(
    "filename,content,category,command,kind",
    [
        ("Makefile", "test:\n\techo ok\n", "test", "make test", "declared"),
        ("go.mod", "module example.org/demo\n", "test", "go test ./...", "inferred"),
        ("Cargo.toml", '[package]\nname="demo"\nversion="0.1.0"', "build", "cargo build", "inferred"),
        ("pom.xml", "<project/>", "test", "mvn test", "inferred"),
        ("build.gradle.kts", "plugins { java }", "test", "gradle test", "inferred"),
        ("Gemfile", "gem 'rubocop'", "lint", "bundle exec rubocop", "inferred"),
        ("composer.json", '{"scripts":{"test":"phpunit"}}', "test", "composer run test", "declared"),
    ],
)
def test_existing_language_sources(tmp_path, filename, content, category, command, kind):
    (tmp_path / filename).write_text(content, encoding="utf-8")
    commands = extract_commands(tmp_path)
    assert command in commands.generation_dict()[category]
    item = next(
        item for item in commands.evidence_dict() if item["command"] == command and item["category"] == category
    )
    assert any(source["path"] == filename and source["kind"] == kind for source in item["sources"])


@pytest.mark.parametrize(
    "filename,content,language,unsupported",
    [
        ("go.mod", "module example.org/demo", "Go", "golangci-lint run"),
        ("Gemfile", "source 'https://example.org'", "Ruby", "bundle exec rubocop"),
        ("pom.xml", "<project/>", "Java", "mvn checkstyle:check"),
    ],
)
def test_optional_tools_need_declarations(tmp_path, filename, content, language, unsupported):
    (tmp_path / filename).write_text(content, encoding="utf-8")
    commands = extract_commands(tmp_path, get_language_profile(language))
    assert unsupported not in commands.generation_dict()["lint"]
    if language == "Java":
        assert all("gradle" not in command for group in commands.to_dict().values() for command in group)


@pytest.mark.parametrize(
    "filename,content",
    [
        ("package.json", "[]"),
        ("package.json", '{"scripts":42}'),
        ("composer.json", '{"scripts":[]}'),
        ("pyproject.toml", "[invalid"),
        ("Cargo.toml", "[invalid"),
        ("pom.xml", "<project>"),
    ],
)
def test_malformed_manifests_are_tolerated_and_reported(tmp_path, filename, content):
    (tmp_path / filename).write_text(content, encoding="utf-8")
    commands = extract_commands(tmp_path)
    assert any(issue["rule_id"] == "SRC001" and issue["path"] == filename for issue in commands.issues)


def test_java_without_manifest_does_not_guess_build_system(tmp_path):
    commands = extract_commands(tmp_path, get_language_profile("Java"))
    assert not any(commands.to_dict().values())
    assert commands.setup == []


@pytest.mark.parametrize(
    "content,declared",
    [
        ("// github.com/golangci/golangci-lint/v2 v2.1.0\nmodule example.org/demo", False),
        ("module example.org/demo\nrequire github.com/golangci/golangci-lint/v2 v2.1.0", True),
        ("module example.org/demo\nrequire (\n github.com/golangci/golangci-lint/v2 v2.1.0\n)", True),
    ],
)
def test_go_optional_tool_requires_actual_dependency(tmp_path, content, declared):
    (tmp_path / "go.mod").write_text(content, encoding="utf-8")
    commands = extract_commands(tmp_path)
    assert ("golangci-lint run" in commands.generation_dict()["lint"]) == declared


@pytest.mark.parametrize(
    "filename,content",
    [
        ("package.json", "[]"),
        ("package.json", '{"dependencies":42}'),
        ("composer.json", "[]"),
        ("composer.json", '{"require":42}'),
    ],
)
def test_analysis_v1_tolerates_malformed_manifest_structure(tmp_path, filename, content):
    import jsonschema

    from repoize.analyzer.project_analyzer import analyze_project
    from repoize.cli import SCHEMA_PATH

    (tmp_path / filename).write_text(content, encoding="utf-8")
    (tmp_path / ("main.php" if filename == "composer.json" else "main.js")).write_text("", encoding="utf-8")
    report = analyze_project(tmp_path).to_dict()
    jsonschema.validate(report, json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig")))
    assert set(report["commands"]) == {"build", "test", "lint", "format", "run"}


def test_poetry_setup_does_not_claim_undeclared_pip_dev_extra(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nname="demo"\n[tool.poetry.dev-dependencies]\npytest="*"', encoding="utf-8"
    )
    commands = extract_commands(tmp_path)
    assert commands.setup == ["pip install -e ."]


def test_npm_default_runner_basis_and_same_manager_locks(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts":{"test":"echo ok"}}', encoding="utf-8")
    item = next(item for item in extract_commands(tmp_path).evidence_dict() if item["category"] == "test")
    assert any("npm default" in (source["selector"] or "") for source in item["sources"])
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / "npm-shrinkwrap.json").write_text("{}", encoding="utf-8")
    commands = extract_commands(tmp_path)
    assert commands.test == ["npm run test"]
    assert commands.issues == []


@pytest.mark.parametrize(
    "fixture,declared",
    [
        ("line-comment.gradle", False),
        ("block-comment.gradle", False),
        ("declared.gradle", True),
    ],
)
def test_gradle_plugin_evidence_ignores_comments(tmp_path, fixture, declared):
    source = Path(__file__).parent / "fixtures/commands/gradle" / fixture
    (tmp_path / "build.gradle").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    commands = extract_commands(tmp_path)
    assert ("gradle spotlessApply" in commands.generation_dict()["format"]) == declared
    evidence = next(item for item in commands.evidence_dict() if item["command"] == "gradle spotlessApply")
    assert {source["kind"] for source in evidence["sources"]} == {"inferred" if declared else "suggested"}


@pytest.mark.parametrize(
    "requirement",
    [
        "pytest@https://example.test/pytest.whl",
        "pytest @ https://example.test/pytest.whl",
        "pytest[extra]@https://example.test/pytest.whl",
        "pytest[extra]>=7",
        "pytest>=7",
    ],
)
def test_pep508_direct_reference_and_extras_keep_dependency_evidence(tmp_path, requirement):
    (tmp_path / "pyproject.toml").write_text(f"[project]\ndependencies={json.dumps([requirement])}", encoding="utf-8")
    commands = extract_commands(tmp_path)
    assert commands.generation_dict()["test"] == ["pytest"]
    evidence = next(item for item in commands.evidence_dict() if item["command"] == "pytest")
    assert evidence["sources"] == [{"kind": "inferred", "path": "pyproject.toml", "selector": "project.dependencies"}]


def test_gradle_string_containing_plugin_text_is_not_a_declaration(tmp_path):
    (tmp_path / "build.gradle.kts").write_text(
        "val note = 'id \"com.diffplug.spotless\"'\nplugins { java }", encoding="utf-8"
    )
    assert extract_commands(tmp_path).generation_dict()["format"] == []
