"""生成器模块测试 - 提高覆盖率"""

import tempfile
from pathlib import Path

from repoize.analyzer.project_analyzer import analyze_project
from repoize.generator.claude_md import ClaudeMdGenerator
from repoize.generator.copilot import CopilotGenerator
from repoize.generator.cursorrules import CursorRulesGenerator
from repoize.generator.mcp_config import McpConfigGenerator
from repoize.generator.skill_md import SkillMdGenerator


def _create_sample_project(tmp_path: Path) -> Path:
    """创建示例项目。"""
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["fastapi", "uvicorn"]
""")
    (tmp_path / "main.py").write_text("print('hello')")
    return tmp_path


def test_claude_md_generator():
    """测试 ClaudeMdGenerator。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        _create_sample_project(project_path)

        analysis = analyze_project(project_path, scan_env=False)
        gen = ClaudeMdGenerator(analysis)

        assert gen.name == "CLAUDE.md"
        assert gen.output_filename == "CLAUDE.md"

        content = gen.generate()
        assert project_path.name in content or "Python" in content


def test_copilot_generator():
    """测试 CopilotGenerator。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        _create_sample_project(project_path)

        analysis = analyze_project(project_path, scan_env=False)
        gen = CopilotGenerator(analysis)

        assert gen.name == "copilot-instructions.md"
        assert gen.output_filename == ".github/copilot-instructions.md"

        content = gen.generate()
        assert project_path.name in content or "Python" in content


def test_cursorrules_generator():
    """测试 CursorRulesGenerator。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        _create_sample_project(project_path)

        analysis = analyze_project(project_path, scan_env=False)
        gen = CursorRulesGenerator(analysis)

        assert gen.name == ".cursorrules"
        assert gen.output_filename == ".cursor/rules/repoize.mdc"

        content = gen.generate()
        assert project_path.name in content or "Python" in content


def test_mcp_config_generator():
    """测试 McpConfigGenerator。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        _create_sample_project(project_path)

        analysis = analyze_project(project_path, scan_env=False)
        gen = McpConfigGenerator(analysis)

        assert gen.name == "MCP 配置"
        assert gen.output_filename == ".mcp.json"

        content = gen.generate()
        assert "mcpServers" in content


def test_skill_md_generator():
    """测试 SkillMdGenerator。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        _create_sample_project(project_path)

        analysis = analyze_project(project_path, scan_env=False)
        gen = SkillMdGenerator(analysis)

        assert gen.name == "SKILL.md"
        assert gen.output_filename == ".claude/skills/project-dev/SKILL.md"

        content = gen.generate()
        assert project_path.name in content or "Python" in content
