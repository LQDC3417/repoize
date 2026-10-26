"""v0.1.2 格式兼容与写入边界合同。"""

import json
import os
import subprocess
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from repoize.analyzer.config_scanner import scan_existing_configs
from repoize.analyzer.env_scanner import EnvInfo, scan_environment
from repoize.analyzer.project_analyzer import ProjectAnalysis, analyze_project
from repoize.cli import main
from repoize.formats import split_frontmatter
from repoize.generator.agents_md import AgentsMdGenerator
from repoize.generator.base import GENERATED_END, GENERATED_START
from repoize.generator.cursorrules import CursorRulesGenerator
from repoize.generator.mcp_config import McpConfigGenerator
from repoize.generator.skill_md import SkillMdGenerator


@pytest.fixture
def analysis(tmp_path):
    return ProjectAnalysis(project_path=tmp_path, project_name='测试: "quoted"')


def test_new_mcp_target_is_empty_json(analysis):
    gen = McpConfigGenerator(analysis)
    assert gen.output_filename == ".mcp.json"
    assert json.loads(gen.generate()) == {"mcpServers": {}}


@pytest.mark.parametrize("generator", [SkillMdGenerator, CursorRulesGenerator])
def test_frontmatter_precedes_markers_and_update_preserves_header(tmp_path, analysis, generator):
    gen = generator(analysis)
    output = gen.write(tmp_path)
    content = output.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert content.index("---", 3) < content.index(GENERATED_START)
    if generator is SkillMdGenerator:
        assert "name: project-dev\n" in content
        assert "license:" not in content
    else:
        assert gen.output_filename == ".cursor/rules/repoize.mdc"
        assert "alwaysApply: true\n" in content
        assert "globs:" not in content
    custom = content.replace("---\n", "---\ncustom: 'retain: exact'\n", 1)
    original = ("\ufeff" + custom.replace("\n", "\r\n")).encode("utf-8")
    output.write_bytes(original)
    before = output.stat().st_mtime_ns
    gen.update(tmp_path)
    assert output.read_bytes() == original
    assert output.stat().st_mtime_ns == before


@pytest.mark.parametrize(
    "markers",
    [
        GENERATED_START,
        GENERATED_END,
        GENERATED_END + GENERATED_START,
        GENERATED_START + GENERATED_START + GENERATED_END,
        GENERATED_START + GENERATED_END + GENERATED_START + GENERATED_END,
    ],
)
def test_malformed_markers_fail_without_write(tmp_path, analysis, markers):
    output = tmp_path / "AGENTS.md"
    output.write_text(markers, encoding="utf-8")
    before = output.read_bytes()
    with pytest.raises(ValueError, match="marker"):
        AgentsMdGenerator(analysis).update(tmp_path)
    assert output.read_bytes() == before


def test_legacy_wrapped_skill_frontmatter_requires_migration(tmp_path, analysis):
    gen = SkillMdGenerator(analysis)
    output = tmp_path / gen.output_filename
    output.parent.mkdir(parents=True)
    original = f"{GENERATED_START}\n---\nname: project-dev\ndescription: old\n---\n{GENERATED_END}"
    output.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="迁移"):
        gen.update(tmp_path)
    assert output.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    ("generator", "header"),
    [
        (SkillMdGenerator, "name: wrong\ndescription: text"),
        (SkillMdGenerator, "name: project-dev\ndescription: [invalid]"),
        (SkillMdGenerator, "name: [project-dev]\ndescription: text"),
        (CursorRulesGenerator, "description: [invalid]\nalwaysApply: true"),
        (CursorRulesGenerator, "description: text\nalwaysApply: 'true'"),
        (CursorRulesGenerator, "description: text\nalwaysApply: true\nglobs: 42"),
        (SkillMdGenerator, "name: project-dev\ndescription: !!python/object/apply:os.system ['echo bad']"),
    ],
)
def test_invalid_frontmatter_is_not_written(tmp_path, analysis, generator, header):
    gen = generator(analysis)
    output = tmp_path / gen.output_filename
    output.parent.mkdir(parents=True)
    original = f"---\n{header}\n---\n{GENERATED_START}\nold\n{GENERATED_END}\n"
    output.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError):
        gen.update(tmp_path)
    assert output.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("operation", ["write", "update"])
def test_refuses_linked_parent_and_target(tmp_path, analysis, operation):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / ".claude"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("此环境不能创建符号链接")
    with pytest.raises((ValueError, OSError)):
        getattr(SkillMdGenerator(analysis), operation)(tmp_path, force=True)
    assert list(outside.iterdir()) == []


def test_refuses_escape_filename(tmp_path, analysis):
    class EscapingGenerator(AgentsMdGenerator):
        output_filename = "../outside.md"

    with pytest.raises(ValueError):
        EscapingGenerator(analysis).write(tmp_path, force=True)


def test_mcp_update_preserves_exact_server_and_unknown_fields(tmp_path, analysis):
    gen = McpConfigGenerator(analysis)
    output = tmp_path / gen.output_filename
    original = b'\xef\xbb\xbf{\r\n  "custom": [1], "mcpServers": {"git": {"url": "https://example.test"}}\r\n}\r\n'
    output.write_bytes(original)
    before = output.stat().st_mtime_ns
    gen.update(tmp_path)
    assert output.read_bytes() == original
    assert output.stat().st_mtime_ns == before


def test_scanner_recognizes_modern_paths_and_only_files(tmp_path):
    (tmp_path / "AGENTS.md").mkdir()
    (tmp_path / ".mcp.json").write_text("{}", encoding="utf-8")
    rules = tmp_path / ".cursor/rules/nested"
    rules.mkdir(parents=True)
    (rules / "custom.mdc").write_text("text", encoding="utf-8")
    (rules / "directory.mdc").mkdir()
    configs = scan_existing_configs(tmp_path)
    existing = {item.path.relative_to(tmp_path).as_posix() for item in configs if item.exists}
    assert ".mcp.json" in existing
    assert ".cursor/rules/nested/custom.mdc" in existing
    assert "AGENTS.md" not in existing
    assert ".cursor/rules/nested/directory.mdc" not in existing
    assert all(set(item.to_dict()) == {"name", "config_type", "exists", "path"} for item in configs)


@pytest.mark.parametrize("command", ["init", "generate", "update"])
@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize(
    ("kind", "legacy", "modern"),
    [
        ("mcp", ".claude/mcp.json", ".mcp.json"),
        ("cursorrules", ".cursorrules", ".cursor/rules/repoize.mdc"),
    ],
)
def test_legacy_only_is_blocked_and_other_types_continue(tmp_path, command, force, kind, legacy, modern):
    old = tmp_path / legacy
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_text("legacy", encoding="utf-8")
    args = [command, str(tmp_path)]
    if command != "update" and force:
        args.append("--force")
    args.extend(["--type", kind, "--type", "agents"])
    if command == "update":
        (tmp_path / "AGENTS.md").write_text(
            f"{GENERATED_START}\nstale managed body\n{GENERATED_END}\n", encoding="utf-8"
        )
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 1, result.output
    assert "迁移" in result.output
    assert not (tmp_path / modern).exists()
    assert old.read_text(encoding="utf-8") == "legacy"
    assert (tmp_path / "AGENTS.md").is_file()
    assert "stale managed body" not in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_mcp_coexistence_preserves_new_and_warns(tmp_path, command):
    legacy = tmp_path / ".claude/mcp.json"
    legacy.parent.mkdir()
    legacy.write_text('{"legacy": true}', encoding="utf-8")
    modern = tmp_path / ".mcp.json"
    original = '{"mcpServers": {"custom": {"url": "https://example.test"}}, "extra": true}'
    modern.write_text(original, encoding="utf-8")
    args = [command, str(tmp_path)]
    if command != "update":
        args.append("--force")
    args.extend(["--type", "mcp"])
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert "并存" in result.output
    if command == "update":
        assert modern.read_text(encoding="utf-8") == original
    else:
        assert json.loads(modern.read_text(encoding="utf-8")) == {"mcpServers": {}}
    assert legacy.read_text(encoding="utf-8") == '{"legacy": true}'


@pytest.mark.parametrize("command", ["init", "generate", "update", "analyze", "check"])
def test_cli_accepts_only_directories(tmp_path, command):
    path = tmp_path / "main.py"
    path.write_text("pass", encoding="utf-8")
    result = CliRunner().invoke(main, [command, str(path)])
    assert result.exit_code == 2


@pytest.mark.parametrize("command", ["init", "generate", "update", "analyze", "check"])
def test_default_cli_never_scans_environment(tmp_path, command):
    args = [command, str(tmp_path)]
    if command == "generate":
        args.extend(["--type", "agents"])
    with patch("repoize.analyzer.project_analyzer.scan_environment", side_effect=AssertionError("环境扫描")):
        result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output


def test_include_env_is_analyze_only_and_excludes_values(tmp_path):
    with patch("repoize.analyzer.project_analyzer.scan_environment", return_value=EnvInfo(system="test")) as scan:
        result = CliRunner().invoke(main, ["analyze", str(tmp_path), "--format", "json", "--include-env"])
    assert result.exit_code == 0, result.output
    assert scan.call_count == 1
    assert json.loads(result.stdout)["env_info"]["system"] == "test"
    result = CliRunner().invoke(main, ["analyze", str(tmp_path), "--include-env", "--no-env"])
    assert result.exit_code == 2


def test_explicit_environment_scan_is_safe_and_sorted(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "sensitive-local-value")
    monkeypatch.setenv("SHELL", "sensitive-shell-path")
    with patch("repoize.analyzer.env_scanner._run_tool_check", side_effect=lambda name, *_: (name, "1.2.3")):
        info = scan_environment()
    assert info.dev_env_vars == {}
    assert info.path_entries == []
    assert info.shell == ""
    assert info.tools == sorted(info.tools)


def test_default_analysis_has_no_environment_and_no_invented_tests(tmp_path):
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    with patch("repoize.analyzer.project_analyzer.scan_environment", side_effect=AssertionError("扫描")):
        analysis = analyze_project(tmp_path)
    assert analysis.env_info == EnvInfo()
    assert analysis.has_tests is False


def test_templates_never_render_local_environment_or_author_preferences(analysis):
    analysis.env_info = EnvInfo(
        tools=[("Python", "sensitive-version-path")], dev_env_vars={"PATH": "secret-local-path"}
    )
    for generator in (AgentsMdGenerator, SkillMdGenerator, CursorRulesGenerator):
        content = generator(analysis).generate()
        assert "secret-local-path" not in content
        assert "sensitive-version-path" not in content
        assert "代码注释使用中文" not in content
        assert "部署的标准流程" not in content


@pytest.mark.parametrize("generator", [SkillMdGenerator, CursorRulesGenerator])
def test_force_replaces_complete_current_target(tmp_path, analysis, generator):
    gen = generator(analysis)
    output = gen.write(tmp_path)
    original = output.read_bytes()
    header, body = original.split(GENERATED_START.encode(), 1)
    header = header.replace(b"---\n", b"---\ncustom: keep\n", 1)
    output.write_bytes(header + GENERATED_START.encode() + body)
    gen.write(tmp_path, force=True)
    assert output.read_bytes() == original


def test_force_replaces_complete_current_mcp(tmp_path, analysis):
    output = tmp_path / ".mcp.json"
    original = '{"custom": 42, "mcpServers": {"remote": {"url": "https://example.test"}}}'
    output.write_text(original, encoding="utf-8")
    McpConfigGenerator(analysis).write(tmp_path, force=True)
    assert json.loads(output.read_text(encoding="utf-8")) == {"mcpServers": {}}


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_cursor_coexistence_is_blocked(tmp_path, analysis, command):
    output = CursorRulesGenerator(analysis).write(tmp_path)
    original = output.read_bytes()
    (tmp_path / ".cursorrules").write_text("old", encoding="utf-8")
    args = [command, str(tmp_path)]
    if command != "update":
        args.append("--force")
    args.extend(["--type", "cursorrules"])
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 1
    assert "迁移" in result.output
    assert output.read_bytes() == original


@pytest.mark.skipif(os.name != "nt", reason="仅验证 Windows junction")
def test_refuses_windows_junction(tmp_path, analysis):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    link = tmp_path / ".claude"
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
    assert result.returncode == 0, result.stderr
    with pytest.raises(ValueError, match="junction"):
        SkillMdGenerator(analysis).write(tmp_path, force=True)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("operation", ["write", "update"])
def test_refuses_symbolic_link_target(tmp_path, analysis, operation):
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("original", encoding="utf-8")
    try:
        (tmp_path / "AGENTS.md").symlink_to(outside)
    except OSError:
        pytest.skip("此环境不能创建符号链接")
    with pytest.raises(ValueError, match="链接"):
        getattr(AgentsMdGenerator(analysis), operation)(tmp_path, force=True)
    assert outside.read_text(encoding="utf-8") == "original"


@pytest.mark.parametrize("name", ["A", "-abc", "abc-", "a--b", "a_b", "a" * 65])
def test_invalid_skill_name_contract(name):
    content = f"---\nname: {name}\ndescription: text\n---\n"
    with pytest.raises(ValueError):
        split_frontmatter(content, f".claude/skills/{name}/SKILL.md")


def test_skill_description_length_and_yaml_errors_hide_source():
    with pytest.raises(ValueError):
        split_frontmatter(
            "---\nname: project-dev\ndescription: " + "x" * 1025 + "\n---\n", ".claude/skills/project-dev/SKILL.md"
        )
    secret = "private-secret-config-value"
    with pytest.raises(ValueError) as error:
        split_frontmatter(
            f"---\nname: project-dev\ndescription: [{secret}\n---\n", ".claude/skills/project-dev/SKILL.md"
        )
    assert secret not in str(error.value)


def test_cursor_globs_accepts_string_array():
    content = '---\ndescription: text\nalwaysApply: false\nglobs: ["*.py", "src/**"]\n---\nbody'
    assert split_frontmatter(content, ".cursor/rules/repoize.mdc")[1] == "body"


def test_profile_suggestions_and_empty_test_directory_are_not_evidence(tmp_path):
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    assert analyze_project(tmp_path).has_tests is False
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    assert analyze_project(tmp_path).has_tests is True


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_wrapped_skill_is_not_silently_skipped(tmp_path, analysis, command):
    gen = SkillMdGenerator(analysis)
    output = tmp_path / gen.output_filename
    output.parent.mkdir(parents=True)
    original = f"{GENERATED_START}\n---\nname: old\ndescription: old\n---\n{GENERATED_END}\n"
    output.write_text(original, encoding="utf-8")
    args = [command, str(tmp_path)]
    args.extend(["--type", "skill"])
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 1
    assert "迁移" in result.output
    assert output.read_text(encoding="utf-8") == original


def test_markers_inside_frontmatter_cannot_change_header(tmp_path, analysis):
    gen = SkillMdGenerator(analysis)
    output = tmp_path / gen.output_filename
    output.parent.mkdir(parents=True)
    content = f"---\nname: project-dev\ndescription: |\n  {GENERATED_START}\n  {GENERATED_END}\n---\nmanual\n"
    output.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="marker"):
        gen.update(tmp_path)
    assert output.read_text(encoding="utf-8") == content


def test_documentation_in_tests_directory_does_not_prove_tests(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "README.md").write_text("TODO: tests", encoding="utf-8")
    assert analyze_project(tmp_path).has_tests is False


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_cli_refuses_symbolic_project_root(tmp_path, command):
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "project-link"
    try:
        link.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("此环境不能创建符号链接")
    args = [command, str(link)]
    if command != "init":
        args.extend(["--type", "agents"])
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 1
    assert list(actual.iterdir()) == []


def test_score_counts_modern_and_legacy_config_once(tmp_path):
    for name in (".mcp.json", ".claude/mcp.json", ".cursorrules", ".cursor/rules/a.mdc", ".cursor/rules/b.mdc"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    assert analyze_project(tmp_path).agent_ready_score == 35


@pytest.mark.parametrize("command", ["init", "generate"])
def test_mcp_coexistence_without_force_warns_and_skips(tmp_path, analysis, command):
    legacy = tmp_path / ".claude/mcp.json"
    legacy.parent.mkdir()
    legacy.write_text("{}", encoding="utf-8")
    modern = tmp_path / ".mcp.json"
    original = '{"custom": 42}'
    modern.write_text(original, encoding="utf-8")
    args = [command, str(tmp_path)]
    args.extend(["--type", "mcp"])
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    assert "并存" in result.output
    assert "跳过 .mcp.json" in result.output
    assert modern.read_text(encoding="utf-8") == original
    with pytest.raises(FileExistsError):
        McpConfigGenerator(analysis).write(tmp_path)


def test_cursor_profile_defaults_are_excluded_from_generated_commands(tmp_path):
    """单文件项目的画像建议不能写成已配置或必须执行的命令。"""
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    analysis = analyze_project(tmp_path)
    content = CursorRulesGenerator(analysis).generate()
    assert analysis.has_tests is False
    assert "运行:" not in content
    assert analysis.profile is not None
    commands = [
        *analysis.profile.setup_commands,
        *analysis.commands.test,
        *analysis.commands.lint,
        *analysis.commands.format,
    ]
    assert commands
    for command in commands:
        assert command not in content
