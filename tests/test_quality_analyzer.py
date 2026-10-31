"""代码质量分析器测试"""

import builtins
import os
import subprocess
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


@pytest.mark.parametrize("link_kind", ["file", "directory", "junction"])
def test_quality_never_reads_linked_external_code(tmp_path, monkeypatch, link_kind):
    """统计、复杂度和重复检测均不得读取链接指向的仓库外代码。"""
    if link_kind == "junction" and os.name != "nt":
        pytest.skip("仅验证 Windows junction")
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    content = "def sample():\n    return 1\n"
    external = outside / "external.py"
    external.write_text(content, encoding="utf-8")
    (project / "main.py").write_text(content, encoding="utf-8")
    link = project / ("linked.py" if link_kind == "file" else "linked")
    if link_kind == "junction":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
        assert result.returncode == 0, result.stderr
    else:
        try:
            link.symlink_to(external if link_kind == "file" else outside, target_is_directory=link_kind == "directory")
        except OSError:
            pytest.skip("此环境不能创建符号链接")
    original = builtins.open

    def guarded(file, *args, **kwargs):
        if isinstance(file, (str, os.PathLike)):
            assert not Path(file).resolve().is_relative_to(outside)
        return original(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded)
    metrics = analyze_code_quality(project)
    assert metrics.total_files == 1
    assert metrics.total_lines == 2
    assert metrics.duplicate_files == 0
    assert metrics.max_function_length > 0


@pytest.mark.parametrize("filename", ["pyproject.toml", "setup.cfg", ".flake8"])
def test_linked_quality_configuration_is_not_read_or_counted(tmp_path, monkeypatch, filename):
    """质量工具检测同样不得读取或采信外部配置链接。"""
    project = tmp_path / "project"
    project.mkdir()
    external = tmp_path / "external.cfg"
    external.write_text("[tool.ruff]\n[flake8]\nmax-line-length = 99\n", encoding="utf-8")
    try:
        (project / filename).symlink_to(external)
    except OSError:
        pytest.skip("此环境不能创建符号链接")
    original = Path.read_text

    def guarded(self, *args, **kwargs):
        assert self.resolve() != external
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    metrics = analyze_code_quality(project)
    assert metrics.quality_tools_found == []
    assert metrics.quality_config_found == []


@pytest.mark.parametrize("directory", ["env", ".tox", ".nox", "third_party", "external"])
def test_quality_excludes_dependency_directories(tmp_path, monkeypatch, directory):
    """质量统计与语言检测使用相同的依赖目录排除规则。"""
    content = "def sample():\n    return 1\n"
    (tmp_path / "main.py").write_text(content, encoding="utf-8")
    ignored = tmp_path / directory
    ignored.mkdir()
    (ignored / "dependency.py").write_text(content, encoding="utf-8")
    original = builtins.open

    def guarded(file, *args, **kwargs):
        if isinstance(file, (str, os.PathLike)):
            assert not Path(file).resolve().is_relative_to(ignored)
        return original(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded)
    metrics = analyze_code_quality(tmp_path)
    assert metrics.total_files == 1
    assert metrics.total_lines == 2
    assert metrics.duplicate_files == 0


@pytest.mark.parametrize(
    "content,expected",
    [
        ("[metadata]\nname = sample\n", False),
        ("[metadata]\ndescription = [flake8]\n", False),
        ("# [flake8]\n[metadata]\nname = sample\n", False),
        ("[flake8\nmax-line-length = 99\n", False),
        ("[flake8]\nmax-line-length = 99\n", True),
        ("[flake8]\nignore = %(custom)s\n", True),
    ],
)
def test_setup_cfg_requires_real_flake8_section(tmp_path, content, expected):
    """共享配置按实际配置节识别 Flake8，不按文件名或注释识别。"""
    (tmp_path / "setup.cfg").write_text(content, encoding="utf-8-sig")
    metrics = analyze_code_quality(tmp_path)
    assert ("flake8" in metrics.quality_tools_found) is expected
    assert ("setup.cfg" in metrics.quality_config_found) is expected


def test_packaging_metadata_does_not_inflate_quality_score(tmp_path):
    """仅增加打包元数据不能提高质量评分。"""
    from repoize.analyzer.project_analyzer import analyze_project

    (tmp_path / "app.py").write_text("print(1)\n", encoding="utf-8")
    baseline = analyze_project(tmp_path).code_quality_score
    (tmp_path / "setup.cfg").write_text("[metadata]\nname = sample\n", encoding="utf-8")
    assert analyze_project(tmp_path).code_quality_score == baseline


@pytest.mark.parametrize("section", ["tool:pytest", "coverage:run", "mypy", "isort"])
def test_setup_cfg_preserves_other_quality_configuration(tmp_path, section):
    """其他真实质量配置仍计入配置覆盖，但不能误认作 Flake8。"""
    (tmp_path / "setup.cfg").write_text(f"[{section}]\n", encoding="utf-8")
    metrics = analyze_code_quality(tmp_path)
    assert metrics.quality_tools_found == []
    assert metrics.quality_config_found == ["setup.cfg"]
