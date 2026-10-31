"""只读诊断合同：退出码、格式、安全边界和旧 JSON 兼容。"""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import jsonschema
import pytest
from click.testing import CliRunner

from repoize.cli import main
from repoize.formats import GENERATED_END, GENERATED_START


def invoke(project, *args):
    return CliRunner().invoke(main, ["doctor", str(project), "--format", "json", *args])


def write(project, filename, content):
    path = project / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_auto_empty_warns_and_strict_fails(tmp_path):
    result = invoke(tmp_path)
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["selected_types"] == []
    assert report["summary"]["warnings"] == 1
    assert "No supported" in report["findings"][0]["message"]
    assert invoke(tmp_path, "--strict").exit_code == 1


def test_only_selected_existing_tool_is_required(tmp_path):
    write(tmp_path, "AGENTS.md", "# Instructions\n")
    for args in ((), ("--type", "agents")):
        result = invoke(tmp_path, *args)
        assert result.exit_code == 0, result.output
        report = json.loads(result.stdout)
        assert report["selected_types"] == ["agents"]
        assert report["summary"]["errors"] == 0
    result = invoke(tmp_path, "--type", "claude")
    assert result.exit_code == 1
    assert json.loads(result.stdout)["findings"][0]["rule_id"] == "CFG001"


def test_aliases_deduplicate_and_diagnostics_sort(tmp_path):
    write(tmp_path, ".cursor/rules/z.mdc", "---\nalwaysApply: 'true'\n---\ntext")
    write(tmp_path, ".cursor/rules/a.mdc", "---\ndescription: 1\n---\ntext")
    result = invoke(tmp_path, "--type", "cursor", "--type", "cursorrules")
    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["selected_types"] == ["cursor"]
    assert [finding["path"] for finding in report["findings"]] == [".cursor/rules/a.mdc", ".cursor/rules/z.mdc"]
    assert {finding["rule_id"] for finding in report["findings"]} == {"CFG006"}


@pytest.mark.parametrize(
    "filename,content,rule_id,severity",
    [
        ("AGENTS.md", "\n ", "CFG003", "error"),
        ("AGENTS.md", GENERATED_START, "UPD001", "error"),
        ("AGENTS.md", GENERATED_END + GENERATED_START, "UPD001", "error"),
        (".cursorrules", "legacy", "CFG002", "warning"),
        (".claude/mcp.json", '{"mcpServers":{"a":{}}}', "CFG002", "warning"),
        (".mcp.json", "[]", "CFG004", "error"),
        (".mcp.json", '{"mcpServers":[]}', "CFG004", "error"),
        (".mcp.json", '{"mcpServers":{"bad":[]}}', "CFG004", "error"),
        (".mcp.json", '{"mcpServers":{}}', "CFG007", "warning"),
        (".mcp.json", "{}", "CFG007", "warning"),
        (".mcp.json", '{"mcpServers":{"empty":{}}}', "CFG007", "warning"),
        (".claude/skills/demo/SKILL.md", "---\nname: wrong\ndescription: text\n---\nbody", "CFG005", "error"),
        (".claude/skills/demo/SKILL.md", "---\nname: demo\ndescription: []\n---\nbody", "CFG005", "error"),
        (".claude/skills/demo/SKILL.md", "body", "CFG005", "error"),
        (
            ".claude/skills/demo/SKILL.md",
            "---\nname: demo\ndescription: [secret-test-value\n---\nbody",
            "CFG004",
            "error",
        ),
        (".cursor/rules/demo.mdc", "---\nalwaysApply: 'true'\n---\nbody", "CFG006", "error"),
        (".cursor/rules/demo.mdc", "---\nglobs: [1]\n---\nbody", "CFG006", "error"),
        (".cursor/rules/demo.mdc", "---\n- item\n---\nbody", "CFG004", "error"),
    ],
)
def test_configuration_findings(tmp_path, filename, content, rule_id, severity):
    write(tmp_path, filename, content)
    result = invoke(tmp_path)
    assert result.exit_code == (1 if severity == "error" else 0), result.output
    findings = json.loads(result.stdout)["findings"]
    assert any(
        item["rule_id"] == rule_id and item["severity"] == severity and item["path"] == filename for item in findings
    )
    assert "secret-test-value" not in result.output


@pytest.mark.parametrize(
    "filename,content",
    [
        (".claude/skills/demo/SKILL.md", "---\nname: demo\ndescription: text\n---\nbody"),
        (".cursor/rules/nested/demo.mdc", '---\nglobs: ["*.py"]\nalwaysApply: false\n---\nbody'),
        (".mcp.json", '{"custom":42,"mcpServers":{"remote":{"url":"https://example.test","extra":true}}}'),
    ],
)
def test_valid_formats(tmp_path, filename, content):
    write(tmp_path, filename, content)
    result = invoke(tmp_path, "--strict")
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["findings"] == []


def test_schema_and_readonly_without_subprocesses(tmp_path, monkeypatch):
    write(tmp_path, "AGENTS.md", f"{GENERATED_START}\ntext\n{GENERATED_END}\n")
    write(tmp_path, "main.py", "pass")
    write(tmp_path, "package.json", '{"scripts":{"test":"echo secret-test-value"}}')
    before = {
        str(path.relative_to(tmp_path)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories = {str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*") if path.is_dir()}
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, lambda *a, **k: pytest.fail("doctor started a process"))
    with patch("repoize.cli.analyze_project", side_effect=AssertionError("full analysis")):
        first = invoke(tmp_path)
        second = invoke(tmp_path)
    assert first.exit_code == 0, first.output
    assert first.stdout == second.stdout
    assert "\x1b" not in first.stdout
    assert "secret-test-value" not in first.output
    report = json.loads(first.stdout)
    schema = json.loads(
        (Path(__file__).parents[1] / "src/repoize/schemas/doctor.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(report, schema)
    assert report["report_type"] == "doctor"
    assert all(item["verification"] == "not_run" for item in report["command_evidence"])
    assert before == {
        str(path.relative_to(tmp_path)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert directories == {str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*") if path.is_dir()}


def test_broken_source_is_error_without_secret(tmp_path):
    write(tmp_path, "AGENTS.md", "text")
    write(tmp_path, "package.json", '{"secret-test-value":')
    result = invoke(tmp_path)
    assert result.exit_code == 1
    assert any(item["rule_id"] == "SRC001" for item in json.loads(result.stdout)["findings"])
    assert "secret-test-value" not in result.output


def test_decoding_and_read_errors_are_findings(tmp_path, monkeypatch):
    path = write(tmp_path, "AGENTS.md", "text")
    path.write_bytes(b"\xff")
    assert invoke(tmp_path).exit_code == 1
    original = Path.read_text

    def blocked(self, *args, **kwargs):
        if self.name == "AGENTS.md":
            raise PermissionError("secret-test-value")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", blocked)
    result = invoke(tmp_path)
    assert result.exit_code == 1
    assert "secret-test-value" not in result.output
    assert json.loads(result.stdout)["findings"][0]["rule_id"] == "CFG003"


def test_bad_path_and_runtime_exit_codes(tmp_path):
    path = write(tmp_path, "file", "x")
    assert invoke(path).exit_code == 2
    assert invoke(tmp_path / "missing").exit_code == 2
    assert invoke(tmp_path, "--type", "unsupported").exit_code == 2
    with patch("repoize.doctor.scan_existing_configs", side_effect=OSError("secret-test-value")):
        result = invoke(tmp_path)
    assert result.exit_code == 3
    assert "secret-test-value" not in result.output


def test_external_link_contents_are_never_read(tmp_path, monkeypatch):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    write(outside, "demo/SKILL.md", "secret-test-value")
    (tmp_path / ".claude").mkdir()
    link = tmp_path / ".claude/skills"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Cannot create symbolic links")
    original = Path.read_text

    def guarded(self, *args, **kwargs):
        assert not self.resolve().is_relative_to(outside)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    result = invoke(tmp_path, "--type", "skill")
    assert result.exit_code == 1
    assert "secret-test-value" not in result.output


@pytest.mark.skipif(os.name != "nt", reason="Windows junction contract")
def test_external_junction_is_not_traversed(tmp_path, monkeypatch):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    write(outside, "rules/leak.mdc", "secret-test-value")
    link = tmp_path / ".cursor"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
    assert result.returncode == 0
    original = Path.read_text

    def guarded(self, *args, **kwargs):
        assert not self.resolve().is_relative_to(outside)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    result = invoke(tmp_path, "--type", "cursor")
    assert result.exit_code == 1
    assert "secret-test-value" not in result.output


def test_unreadable_directory_cannot_claim_complete_scan(tmp_path, monkeypatch):
    write(tmp_path, ".cursor/rules/demo.mdc", "text")

    def blocked(*args, onerror=None, **kwargs):
        if onerror:
            onerror(PermissionError("secret-test-value"))
        return iter(())

    monkeypatch.setattr("repoize.analyzer.config_scanner.os.walk", blocked)
    result = invoke(tmp_path)
    assert result.exit_code == 3
    assert "secret-test-value" not in result.output


def test_marker_inside_frontmatter_is_damaged(tmp_path):
    write(tmp_path, ".cursor/rules/demo.mdc", f"---\ndescription: |\n  {GENERATED_START}\n  {GENERATED_END}\n---\nbody")
    result = invoke(tmp_path)
    assert result.exit_code == 1
    assert json.loads(result.stdout)["findings"][0]["rule_id"] == "UPD001"


def test_linked_manifest_is_not_read(tmp_path, monkeypatch):
    outside = tmp_path.parent / f"{tmp_path.name}-outside.json"
    outside.write_text('{"scripts":{"test":"secret-test-value"}}', encoding="utf-8")
    try:
        (tmp_path / "package.json").symlink_to(outside)
    except OSError:
        pytest.skip("Cannot create symbolic links")
    original = Path.read_text

    def guarded(self, *args, **kwargs):
        assert self.resolve() != outside.resolve()
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    result = invoke(tmp_path)
    assert result.exit_code == 1
    assert any(item["rule_id"] == "SRC001" for item in json.loads(result.stdout)["findings"])


def test_unreadable_source_is_a_safe_finding(tmp_path, monkeypatch):
    write(tmp_path, "Makefile", "test:")
    original = Path.read_text

    def guarded(self, *args, **kwargs):
        if self.name == "Makefile":
            raise OSError("secret-test-value")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    result = invoke(tmp_path)
    assert result.exit_code == 1
    assert "secret-test-value" not in result.output
    assert any(
        item["rule_id"] == "SRC001" and item["path"] == "Makefile" for item in json.loads(result.stdout)["findings"]
    )


def test_scan_metadata_failure_is_a_single_file_finding(tmp_path, monkeypatch):
    write(tmp_path, "AGENTS.md", "text")
    original = Path.stat

    def guarded(self, *args, **kwargs):
        if self.name == "AGENTS.md":
            raise PermissionError("secret-test-value")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", guarded)
    result = invoke(tmp_path)
    assert result.exit_code == 1
    assert "secret-test-value" not in result.output
    assert any(
        item["rule_id"] == "CFG003" and item["path"] == "AGENTS.md" for item in json.loads(result.stdout)["findings"]
    )


def test_doctor_schema_rejects_unknown_fields_and_nonrelative_paths(tmp_path):
    result = invoke(tmp_path)
    schema = json.loads(
        (Path(__file__).parents[1] / "src/repoize/schemas/doctor.schema.json").read_text(encoding="utf-8")
    )
    report = json.loads(result.stdout)
    report["extra"] = 1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(report, schema)
    del report["extra"]
    for path in ("/outside", "C:/outside", "../outside", "nested/../outside", "nested\\file"):
        report["findings"][0]["path"] = path
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(report, schema)


def test_terminal_output_states_actual_scope(tmp_path):
    write(tmp_path, "CLAUDE.md", "text")
    result = CliRunner().invoke(main, ["doctor", str(tmp_path)])
    assert result.exit_code == 0
    assert "Checked 1 configuration" in result.stdout
    assert "client loading, command execution, and network access were not checked" in result.stdout


@pytest.mark.parametrize(
    "declaration",
    [
        "[project.scripts]\ndemo=42",
        "[project.scripts]\ndemo=''",
        "[tool.poetry.scripts]\ndemo=42",
        "[tool.poetry.scripts]\ndemo={reference=42}",
        "[tool.poetry.scripts]\ndemo={type='console'}",
        "[tool.ruff]\n[tool]\npytest=42",
        "[project]\ndependencies=[42]",
        "[project]\ndependencies={pytest='*'}",
        "[project.optional-dependencies]\ndev=[42]",
        "[tool.poetry.dependencies]\npytest=42",
    ],
)
def test_invalid_extracted_python_fields_are_source_findings(tmp_path, declaration):
    write(tmp_path, "AGENTS.md", "text")
    write(tmp_path, "pyproject.toml", declaration)
    result = invoke(tmp_path)
    assert result.exit_code == 1, result.output
    assert any(
        item["rule_id"] == "SRC001" and item["path"] == "pyproject.toml"
        for item in json.loads(result.stdout)["findings"]
    )
    assert not any(item["command"] == "pytest" for item in json.loads(result.stdout)["command_evidence"])


@pytest.mark.parametrize("filename", [".cursor/rules/demo.mdc", ".claude/skills/demo/SKILL.md"])
def test_nested_metadata_failure_is_a_file_finding(tmp_path, monkeypatch, filename):
    path = write(tmp_path, filename, "text")
    original = Path.lstat

    def guarded(self, *args, **kwargs):
        if self == path:
            raise PermissionError("secret-test-value")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", guarded)
    result = invoke(tmp_path)
    assert result.exit_code == 1, result.output
    report = json.loads(result.stdout)
    assert report["summary"]["checked_files"] == 1
    assert any(item["rule_id"] == "CFG003" and item["path"] == filename for item in report["findings"])
    assert "secret-test-value" not in result.output


def test_root_enumeration_failure_is_runtime_failure_but_analysis_stays_tolerant(tmp_path, monkeypatch):
    from repoize.analyzer.project_analyzer import analyze_project

    write(tmp_path, "AGENTS.md", "text")
    original = Path.iterdir

    def guarded(self, *args, **kwargs):
        if self == tmp_path:
            raise PermissionError("secret-test-value")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "iterdir", guarded)
    result = invoke(tmp_path)
    assert result.exit_code == 3
    assert "secret-test-value" not in result.output
    assert analyze_project(tmp_path).project_name == tmp_path.name


def test_terminal_shows_type_evidence_fixes_and_declared_command_sources(tmp_path):
    write(tmp_path, "AGENTS.md", "text")
    write(tmp_path, "pyproject.toml", "[project.scripts]\ndemo='app:main'")
    write(tmp_path, "Makefile", "test:\n\techo secret-test-value")
    result = CliRunner().invoke(main, ["doctor", str(tmp_path), "--type", "claude", "--type", "copilot"])
    assert result.exit_code == 1
    assert "type=claude" in result.stdout
    assert "type=copilot" in result.stdout
    assert "Evidence:" in result.stdout
    assert "Fix: Create an entry" in result.stdout
    assert "run: demo" in result.stdout
    assert "test: make test" in result.stdout
    assert "verification=not_run" in result.stdout
    assert "kind=declared path=pyproject.toml selector=project.scripts.demo" in result.stdout
    assert "kind=declared path=Makefile selector=test" in result.stdout
    assert "secret-test-value" not in result.output


@pytest.mark.parametrize(
    "filename,content",
    [
        ("mcp.json", '{"mcpServers":{"demo":{"url":"https://example.test"}}}'),
        ("claude_desktop_config.json", '{"mcpServers":{"demo":{"url":"https://example.test"}}}'),
        ("SKILL.md", "---\nname: demo\ndescription: text\n---\nbody"),
    ],
)
def test_supported_generic_entries_are_not_claimed_legacy(tmp_path, filename, content):
    project = tmp_path / "demo"
    project.mkdir()
    write(project, filename, content)
    result = invoke(project, "--strict")
    assert result.exit_code == 0, result.output
    assert not any(item["rule_id"] == "CFG002" for item in json.loads(result.stdout)["findings"])


def test_root_metadata_io_failure_uses_runtime_exit_code(tmp_path, monkeypatch):
    original = Path.lstat

    def guarded(self, *args, **kwargs):
        if self == tmp_path:
            raise PermissionError("secret-test-value")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", guarded)
    result = invoke(tmp_path)
    assert result.exit_code == 3
    assert "secret-test-value" not in result.output
    assert "without links or reparse points" not in result.output


def test_root_link_is_still_a_path_parameter_error(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("Cannot create symbolic links")
    assert invoke(link).exit_code == 2


@pytest.mark.parametrize(
    "filename,kind", [(".cursor/rules/demo.mdc", "cursor"), (".claude/skills/demo/SKILL.md", "skill")]
)
@pytest.mark.parametrize("selection", [(), ("--type",)])
@pytest.mark.parametrize("target_kind", ["internal", "external", "missing"])
def test_nested_file_links_are_diagnosed_without_reading_targets(
    tmp_path, monkeypatch, filename, kind, selection, target_kind
):
    """严格诊断保留链接条目并报 CFG003，自动发现和显式类型行为一致。"""
    write(tmp_path, "AGENTS.md", "text")
    target = tmp_path.parent / f"{tmp_path.name}-outside.txt" if target_kind == "external" else tmp_path / "source.txt"
    if target_kind != "missing":
        target.write_text("secret-test-value", encoding="utf-8")
    link = tmp_path / filename
    link.parent.mkdir(parents=True)
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("此环境不能创建符号链接")
    original = Path.read_text

    def guarded(self, *args, **kwargs):
        assert self.resolve() != target
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    options = (*selection, kind) if selection else ()
    result = invoke(tmp_path, "--strict", *options)
    assert result.exit_code == 1, result.output
    report = json.loads(result.stdout)
    assert any(item["rule_id"] == "CFG003" and item["path"] == filename for item in report["findings"])
    assert not any(item["rule_id"] == "CFG001" for item in report["findings"])
    assert "secret-test-value" not in result.output
