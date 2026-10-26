"""候选变更、只读预览和检查合同。"""

import json
import os
from pathlib import Path

import jsonschema
import pytest
from click.testing import CliRunner

from repoize.analyzer.project_analyzer import analyze_project
from repoize.cli import main
from repoize.generator.agents_md import AgentsMdGenerator
from repoize.targets import GENERATOR_MAP


def invoke(root, command, *args):
    return CliRunner().invoke(main, [command, str(root), *args])


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
        for p in [root, *root.rglob("*")]
    }


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_dry_run_is_readonly_json_schema(tmp_path, command):
    if command == "update":
        invoke(tmp_path, "init")
        (tmp_path / "main.py").write_text("pass\n", encoding="utf-8")
    before = snapshot(tmp_path)
    result = invoke(tmp_path, command, "--type", "agents", "--type", "skill", "--dry-run", "--format", "json")
    assert result.exit_code == (1 if command == "update" else 0), result.output
    data = json.loads(result.stdout)
    schema = json.loads((Path(__file__).parents[1] / "src/repoize/schemas/changes.schema.json").read_text())
    jsonschema.validate(data, schema)
    assert data["report_type"] == "changes"
    assert snapshot(tmp_path) == before
    assert "old_bytes" not in result.stdout


@pytest.mark.parametrize("args", [["--diff"], ["--diff", "--dry-run", "--format", "json"], ["--check", "--dry-run"]])
def test_invalid_preview_combinations(tmp_path, args):
    assert invoke(tmp_path, "update", *args).exit_code == 2


def test_all_types_immediately_fresh_and_check_readonly(tmp_path):
    args = [item for kind in GENERATOR_MAP for item in ("--type", kind)]
    result = invoke(tmp_path, "init", *args)
    assert result.exit_code == 0, result.output
    before = snapshot(tmp_path)
    result = invoke(tmp_path, "update", "--check", "--format", "json")
    assert result.exit_code == 0, result.output
    assert snapshot(tmp_path) == before
    data = json.loads(result.stdout)
    assert next(c for c in data["changes"] if c["type"] == "mcp")["reason"] == "not_comparable"
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    assert invoke(tmp_path, "update", "--check").exit_code == 1


def test_candidate_guard_and_exact_atomic_bytes(tmp_path):
    gen = AgentsMdGenerator(analyze_project(tmp_path))
    candidate = gen.plan(tmp_path)
    assert not (tmp_path / "AGENTS.md").exists()
    candidate.apply(tmp_path)
    assert (tmp_path / "AGENTS.md").read_bytes() == candidate.new_bytes
    candidate = gen.plan(tmp_path, mode="update")
    (tmp_path / "AGENTS.md").write_text("concurrent edit", encoding="utf-8")
    with pytest.raises(ValueError, match="concurrent"):
        candidate.apply(tmp_path)
    assert (tmp_path / "AGENTS.md").read_text() == "concurrent edit"


@pytest.mark.parametrize(
    "value", ["[]", '{"mcpServers": []}', '{"mcpServers": {"secret-key": "secret-value"}}', '{"secret":']
)
def test_invalid_mcp_force_never_writes_or_leaks(tmp_path, value):
    target = tmp_path / ".mcp.json"
    target.write_text(value, encoding="utf-8")
    result = invoke(tmp_path, "generate", "--type", "mcp", "--force", "--dry-run", "--format", "json")
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["changes"][0]["action"] == "error"
    assert "secret" not in result.output
    assert target.read_text() == value


def test_mcp_force_diff_hides_all_user_keys_values(tmp_path):
    target = tmp_path / ".mcp.json"
    target.write_text(
        '{"private-key": "private-value", "mcpServers": {"private-server": {"env": {"TOKEN": "private-token"}}}}'
    )
    result = invoke(tmp_path, "generate", "--type", "mcp", "--force", "--dry-run", "--diff")
    assert result.exit_code == 0, result.output
    assert "private" not in result.output
    assert "mcpServers" in result.output


@pytest.mark.parametrize("content,code", [(None, 3), ("manual", 3), ("<!-- repoize:generated-start -->", 1)])
def test_check_classification(tmp_path, content, code):
    if content is not None:
        (tmp_path / "AGENTS.md").write_text(content)
    result = invoke(tmp_path, "update", "--type", "agents", "--check", "--format", "json")
    assert result.exit_code == code, result.output
    json.loads(result.stdout)


def test_preview_recomputes_and_actual_applies_same_candidate(tmp_path):
    gen = AgentsMdGenerator(analyze_project(tmp_path))
    first = gen.plan(tmp_path)
    assert first.new_bytes == gen.plan(tmp_path).new_bytes
    preview = invoke(tmp_path, "init", "--dry-run", "--diff")
    assert preview.exit_code == 0
    assert "+<!-- repoize:generated-start -->" in preview.stdout
    (tmp_path / "main.py").write_text("pass")
    second = AgentsMdGenerator(analyze_project(tmp_path)).plan(tmp_path)
    assert second.new_bytes != first.new_bytes
    assert invoke(tmp_path, "init", "--format", "json").exit_code == 0
    assert (tmp_path / "AGENTS.md").read_bytes() == second.new_bytes
    before = snapshot(tmp_path)
    assert invoke(tmp_path, "update").exit_code == 0
    assert snapshot(tmp_path) == before


def test_dry_run_forbids_any_write_attempt(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("dry-run attempted mutation")

    monkeypatch.setattr(Path, "mkdir", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    result = invoke(tmp_path, "init", "--type", "skill", "--dry-run")
    assert result.exit_code == 0, result.output


def test_atomic_failure_cleans_own_temp_and_continues(tmp_path, monkeypatch):
    import repoize.changes as module

    real_replace = module.os.replace

    def replace(source, target):
        if target.name == "AGENTS.md":
            raise OSError("secret filesystem context")
        return real_replace(source, target)

    monkeypatch.setattr(module.os, "replace", replace)
    result = invoke(tmp_path, "init", "--type", "claude", "--format", "json")
    assert result.exit_code == 1
    assert json.loads(result.stdout)["summary"]["error"] == 1
    assert "secret" not in result.output
    assert (tmp_path / "CLAUDE.md").is_file()
    assert not (tmp_path / "AGENTS.md").exists()
    assert not list(tmp_path.rglob(".repoize-*.tmp"))


def test_concurrent_edit_immediately_before_replace_is_refused(tmp_path, monkeypatch):
    import repoize.changes as module

    gen = AgentsMdGenerator(analyze_project(tmp_path))
    gen.write(tmp_path)
    (tmp_path / "main.py").write_text("pass")
    gen = AgentsMdGenerator(analyze_project(tmp_path))
    change = gen.plan(tmp_path, mode="update")
    real_fsync = module.os.fsync

    def fsync(fd):
        (tmp_path / "AGENTS.md").write_text("concurrent edit")
        return real_fsync(fd)

    monkeypatch.setattr(module.os, "fsync", fsync)
    with pytest.raises(ValueError, match="concurrent"):
        change.apply(tmp_path)
    assert (tmp_path / "AGENTS.md").read_text() == "concurrent edit"
    assert not list(tmp_path.rglob(".repoize-*.tmp"))


def test_check_mcp_only_invalid_overrides_drift_and_safe_path(tmp_path):
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {"secret": {"env": {"token": "secret"}}}}')
    result = invoke(tmp_path, "update", "--type", "mcp", "--check", "--format", "json")
    assert result.exit_code == 3
    assert "secret" not in result.output
    invoke(tmp_path, "init")
    (tmp_path / "main.py").write_text("pass")
    (tmp_path / ".mcp.json").write_text("[]")
    assert invoke(tmp_path, "update", "--check").exit_code == 3
    (tmp_path / "AGENTS.md").unlink()
    (tmp_path / "AGENTS.md").mkdir()
    assert invoke(tmp_path, "update", "--check").exit_code == 2


def test_tree_preserves_real_empty_and_custom_context(tmp_path):
    (tmp_path / "empty").mkdir()
    github = tmp_path / ".github"
    github.mkdir()
    (github / "custom.yml").write_text("custom")
    tree = analyze_project(tmp_path).directory_tree
    assert "empty/" in tree
    assert "custom.yml" in tree
    invoke(tmp_path, "init", "--type", "copilot")
    tree = analyze_project(tmp_path).directory_tree
    assert "copilot-instructions.md" not in tree
    assert "custom.yml" in tree
    assert invoke(tmp_path, "update", "--check").exit_code == 0


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_preview_aggregates_bad_format_and_safe_candidate(tmp_path, command):
    (tmp_path / ".mcp.json").write_text('{"secret":')
    if command == "update":
        invoke(tmp_path, "init")
        (tmp_path / "main.py").write_text("pass")
    before = snapshot(tmp_path)
    result = invoke(tmp_path, command, "--type", "agents", "--type", "mcp", "--dry-run", "--format", "json")
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert len(data["changes"]) == 2
    assert data["summary"]["error"] == 1
    assert snapshot(tmp_path) == before
    assert "secret" not in result.output


def test_check_ignores_manual_header_but_detects_repo_declarations(tmp_path):
    invoke(tmp_path, "init", "--type", "skill")
    agents = tmp_path / "AGENTS.md"
    agents.write_bytes(b"manual-prefix\n" + agents.read_bytes() + b"manual-suffix\n")
    skill = tmp_path / ".claude/skills/project-dev/SKILL.md"
    original = skill.read_text(encoding="utf-8").replace("---\n", "---\ncustom: keep\n", 1)
    skill.write_bytes(("\ufeff" + original.replace("\n", "\r\n")).encode())
    assert invoke(tmp_path, "update", "--check").exit_code == 0
    before = snapshot(tmp_path)
    assert invoke(tmp_path, "update").exit_code == 0
    assert snapshot(tmp_path) == before
    (tmp_path / "package.json").write_text('{"scripts": {"test": "echo hi"}}')
    assert invoke(tmp_path, "update", "--check").exit_code == 1
    assert invoke(tmp_path, "update").exit_code == 0
    assert skill.read_bytes().startswith(b"\xef\xbb\xbf---\r\ncustom: keep\r\n")
    assert agents.read_bytes().startswith(b"manual-prefix\n")
    assert agents.read_bytes().endswith(b"manual-suffix\n")


def test_preview_rejects_file_parent(tmp_path):
    (tmp_path / ".claude").write_text("occupied")
    result = invoke(tmp_path, "generate", "--type", "skill", "--dry-run", "--format", "json")
    assert result.exit_code == 1
    assert json.loads(result.stdout)["changes"][0]["reason"] == "invalid_path"


def test_analysis_runtime_failure_is_still_sanitized_json(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("private-value")

    monkeypatch.setattr("repoize.cli.analyze_project", fail)
    result = invoke(tmp_path, "init", "--dry-run", "--format", "json")
    assert result.exit_code == 1
    assert json.loads(result.stdout)["changes"][0]["reason"] == "analysis_failed"
    assert "private" not in result.output


def test_direct_mcp_candidate_never_uses_raw_text_diff(tmp_path):
    from repoize.generator.mcp_config import McpConfigGenerator

    (tmp_path / ".mcp.json").write_text('{"mcpServers": {"private-server": {"url": "private-url"}}}')
    change = McpConfigGenerator(analyze_project(tmp_path)).plan(tmp_path, force=True)
    assert change.type == "mcp"
    assert "private" not in change.diff()
    assert "private" not in json.dumps(change.to_dict())


@pytest.mark.parametrize(
    "kind,path,content",
    [
        ("agents", "AGENTS.md", "<!-- repoize:generated-start -->\nprivate-value"),
        ("skill", ".claude/skills/project-dev/SKILL.md", "---\nname: wrong\ndescription: private-value\n---\nmanual"),
        ("cursor", ".cursor/rules/repoize.mdc", "---\nalwaysApply: private-value\n---\nmanual"),
    ],
)
def test_force_preview_cannot_bypass_damaged_text(tmp_path, kind, path, content):
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    before = snapshot(tmp_path)
    result = invoke(tmp_path, "generate", "--type", kind, "--force", "--dry-run", "--format", "json")
    assert result.exit_code == 1
    assert "private-value" not in result.output
    assert json.loads(result.stdout)["changes"][0]["action"] in {"conflict", "error"}
    assert snapshot(tmp_path) == before


def test_valid_manual_text_skip_force_preview_and_exact_apply(tmp_path):
    target = tmp_path / "AGENTS.md"
    target.write_text("private-manual-text", encoding="utf-8")
    result = invoke(tmp_path, "init", "--dry-run", "--format", "json")
    assert result.exit_code == 0
    assert json.loads(result.stdout)["changes"][0]["action"] == "skip"
    force = invoke(tmp_path, "init", "--force", "--dry-run", "--format", "json")
    assert force.exit_code == 0
    assert "private-manual-text" not in force.output
    assert json.loads(force.stdout)["changes"][0]["action"] == "update"
    difference = invoke(tmp_path, "init", "--force", "--dry-run", "--diff")
    assert "-private-manual-text" in difference.stdout
    candidate = AgentsMdGenerator(analyze_project(tmp_path)).plan(tmp_path, force=True)
    assert invoke(tmp_path, "init", "--force").exit_code == 0
    assert target.read_bytes() == candidate.new_bytes


def test_atomic_failure_preserves_existing_file(tmp_path, monkeypatch):
    import repoize.changes as module

    invoke(tmp_path, "init")
    target = tmp_path / "AGENTS.md"
    before = target.read_bytes(), target.stat().st_mtime_ns
    (tmp_path / "main.py").write_text("pass")

    def fail(*args):
        raise OSError("replace unavailable")

    monkeypatch.setattr(module.os, "replace", fail)
    result = invoke(tmp_path, "update", "--type", "agents", "--format", "json")
    assert result.exit_code == 1
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    assert not list(tmp_path.glob(".repoize-*.tmp"))


def test_change_schema_rejects_internal_bytes_unknown_paths_and_statuses(tmp_path):
    import copy

    result = invoke(tmp_path, "init", "--dry-run", "--format", "json")
    report = json.loads(result.stdout)
    schema = json.loads((Path(__file__).parents[1] / "src/repoize/schemas/changes.schema.json").read_text())
    for key, value in [
        ("old_bytes", "private-value"),
        ("path", "C:/outside/file.md"),
        ("reason", "private-value"),
        ("action", "made-up"),
    ]:
        bad = copy.deepcopy(report)
        bad["changes"][0][key] = value
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)


def test_atomic_replace_copies_existing_mode_before_replacement(tmp_path, monkeypatch):
    import stat

    import repoize.changes as module

    target = tmp_path / "AGENTS.md"
    target.write_text("manual", encoding="utf-8")
    expected_mode = stat.S_IMODE(target.stat().st_mode)
    calls = []
    real_chmod = module.os.chmod
    real_replace = module.os.replace

    def chmod(path, mode):
        calls.append((Path(path), mode))
        return real_chmod(path, mode)

    def replace(source, destination):
        assert calls == [(Path(source), expected_mode)]
        return real_replace(source, destination)

    monkeypatch.setattr(module.os, "chmod", chmod)
    monkeypatch.setattr(module.os, "replace", replace)
    change = AgentsMdGenerator(analyze_project(tmp_path)).plan(tmp_path, force=True)
    change.apply(tmp_path)
    assert target.read_bytes() == change.new_bytes
    assert stat.S_IMODE(target.stat().st_mode) == expected_mode
    assert not list(tmp_path.glob(".repoize-*.tmp"))


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not supported on Windows")
@pytest.mark.parametrize("mode", [0o644, 0o750])
def test_atomic_replace_preserves_posix_mode(tmp_path, mode):
    import stat

    target = tmp_path / "AGENTS.md"
    target.write_text("manual", encoding="utf-8")
    target.chmod(mode)
    AgentsMdGenerator(analyze_project(tmp_path)).write(tmp_path, force=True)
    assert stat.S_IMODE(target.stat().st_mode) == mode


def test_atomic_mode_copy_failure_preserves_original_and_cleans_temp(tmp_path, monkeypatch):
    import repoize.changes as module

    target = tmp_path / "AGENTS.md"
    target.write_text("manual", encoding="utf-8")
    before = target.read_bytes(), target.stat().st_mtime_ns

    def fail(*args):
        raise OSError("chmod unavailable")

    monkeypatch.setattr(module.os, "chmod", fail)
    change = AgentsMdGenerator(analyze_project(tmp_path)).plan(tmp_path, force=True)
    with pytest.raises(OSError, match="chmod unavailable"):
        change.apply(tmp_path)
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    assert not list(tmp_path.glob(".repoize-*.tmp"))


@pytest.mark.skipif(os.name != "nt", reason="Windows read-only replacement and cleanup semantics")
def test_readonly_replacement_failure_cleans_only_own_temp(tmp_path):
    import stat

    target = tmp_path / "AGENTS.md"
    target.write_text("manual", encoding="utf-8")
    target.chmod(stat.S_IREAD)
    original = target.read_bytes(), target.stat().st_mode
    change = AgentsMdGenerator(analyze_project(tmp_path)).plan(tmp_path, force=True)
    try:
        with pytest.raises(PermissionError) as error:
            change.apply(tmp_path)
        assert error.value.filename2 == str(target)
        assert (target.read_bytes(), target.stat().st_mode) == original
        assert not list(tmp_path.glob(".repoize-*.tmp"))
    finally:
        target.chmod(stat.S_IWRITE)
