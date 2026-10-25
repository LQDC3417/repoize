"""代码质量分析器测试"""

import tempfile
from pathlib import Path

import pytest

from repoize.analyzer.quality_analyzer import analyze_code_quality


def test_quality_tools_from_bom_and_inline_toml(tmp_path):
    """带 BOM 的内联工具表与常规配置节等价。"""
    content = "[tool]\nruff = {}\nmypy = {}\npytest = {ini_options = {}}\n"
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8-sig")
    assert analyze_code_quality(tmp_path).quality_tools_found == ["mypy", "pytest", "ruff"]


@pytest.mark.parametrize(
    "content",
    [
        "[tool.ruff]\nline-length = ",
        'tool = ["ruff"]',
        '[tool]\nruff = "invalid"\nmypy = false',
        '# [tool.ruff]\n[project]\ndescription = "[tool.mypy]"',
    ],
)
def test_invalid_pyproject_does_not_report_quality_tools(tmp_path, content):
    """错误结构和注释都不算工具配置。"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    assert analyze_code_quality(tmp_path).quality_tools_found == []


def test_analyze_code_quality_empty_project():
    """测试空项目的代码质量分析。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        metrics = analyze_code_quality(project_path)

        assert metrics.total_files == 0
        assert metrics.total_lines == 0
        assert metrics.code_lines == 0


def test_analyze_code_quality_python_project():
    """测试Python项目的代码质量分析。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # 创建一个简单的Python文件
        py_file = project_path / "test.py"
        py_file.write_text('''def hello():
    """Say hello."""
    print("Hello, World!")

def add(a, b):
    """Add two numbers."""
    return a + b
''')

        metrics = analyze_code_quality(project_path)

        assert metrics.total_files == 1
        assert metrics.total_lines > 0
        assert metrics.files_by_language.get("Python") == 1


def test_analyze_code_quality_with_config():
    """测试有配置文件的代码质量分析。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # 创建配置文件
        config_file = project_path / ".flake8"
        config_file.write_text("[flake8]\nmax-line-length = 120\n")

        metrics = analyze_code_quality(project_path)

        assert ".flake8" in metrics.quality_config_found
