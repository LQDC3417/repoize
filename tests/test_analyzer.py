"""项目分析器 + 配置扫描器测试"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from repoize.analyzer.config_scanner import scan_existing_configs
from repoize.analyzer.project_analyzer import analyze_project


def test_analyze_with_env():
    """测试带环境扫描的分析。"""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "main.py").write_text("print('hi')", encoding="utf-8")
    analysis = analyze_project(tmp, scan_env=True)
    assert analysis.env_info.system  # 应有系统信息
    assert len(analysis.env_info.tools) > 0  # 应检测到工具


def test_analyze_without_env():
    """测试不带环境扫描的分析。"""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "main.py").write_text("print('hi')", encoding="utf-8")
    analysis = analyze_project(tmp, scan_env=False)
    assert analysis.env_info.system == ""  # 应为空


def test_config_scanner_detects_claude_md(tmp_path):
    """测试配置扫描器检测 CLAUDE.md。"""
    (tmp_path / "CLAUDE.md").write_text("# test", encoding="utf-8")
    configs = scan_existing_configs(tmp_path)
    claude_cfg = next(c for c in configs if c.config_type == "claude_md")
    assert claude_cfg.exists is True


def test_config_scanner_missing_claude_md(tmp_path):
    """测试配置扫描器检测缺失的 CLAUDE.md。"""
    configs = scan_existing_configs(tmp_path)
    claude_cfg = next(c for c in configs if c.config_type == "claude_md")
    assert claude_cfg.exists is False


def test_analyze_empty_project(tmp_path):
    """测试空项目分析。"""
    analysis = analyze_project(tmp_path, scan_env=False)
    assert analysis.primary_language is None
    assert len(analysis.dependencies) == 0
    assert analysis.has_tests is False
    assert analysis.has_ci is False
    assert analysis.agent_ready_score == 0


def test_analyze_multi_language(tmp_path):
    """测试多语言项目检测。"""
    (tmp_path / "main.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('app')", encoding="utf-8")
    (tmp_path / "index.js").write_text("console.log('hi')", encoding="utf-8")
    analysis = analyze_project(tmp_path, scan_env=False)
    assert analysis.primary_language == "Python"
    assert "JavaScript" in analysis.languages


def test_analyze_with_ci(tmp_path):
    """测试 CI 配置检测。"""
    (tmp_path / "main.py").write_text("print('hi')", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI", encoding="utf-8")
    analysis = analyze_project(tmp_path, scan_env=False)
    assert analysis.has_ci is True


def test_analyze_go_profile(tmp_path):
    """测试 Go 项目匹配 profile 并提取命令。"""
    (tmp_path / "go.mod").write_text("module example.com/foo\n\ngo 1.22\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    analysis = analyze_project(tmp_path, scan_env=False)
    assert analysis.primary_language == "Go"
    assert analysis.profile is not None
    assert "go test ./..." in analysis.commands.test


def test_analyze_frameworks(tmp_path):
    """测试框架识别写入分析结果。"""
    content = """{
  "dependencies": {
    "express": "^4.19.0"
  }
}
"""
    (tmp_path / "package.json").write_text(content, encoding="utf-8")
    (tmp_path / "index.js").write_text("console.log('hi')", encoding="utf-8")
    analysis = analyze_project(tmp_path, scan_env=False)
    assert analysis.frameworks == ["express"]


@pytest.mark.parametrize(
    "dependency_path", [".venv/Lib/site-packages/demo", "node_modules/demo", "vendor/demo", "src/third_party/demo"]
)
def test_dependency_tests_do_not_prove_project_tests(tmp_path, dependency_path):
    """依赖与构建目录里的测试不能作为项目测试证据。"""
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    tests = tmp_path / dependency_path / "tests"
    tests.mkdir(parents=True)
    (tests / "test_core.py").write_text("def test_core(): pass", encoding="utf-8")
    assert analyze_project(tmp_path).has_tests is False


@pytest.mark.parametrize("link_kind", ["directory", "file", "junction"])
def test_external_link_tests_are_not_scanned(tmp_path, link_kind):
    """扫描不得沿目录链接或文件链接读取外部测试。"""
    if link_kind == "junction" and os.name != "nt":
        pytest.skip("仅验证 Windows junction")
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("pass", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    external = outside / "test_external.py"
    external.write_text("def test_external(): pass", encoding="utf-8")
    link = project / ("test_link.py" if link_kind == "file" else "linked")
    if link_kind == "junction":
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
        assert result.returncode == 0, result.stderr
    else:
        try:
            link.symlink_to(external if link_kind == "file" else outside, target_is_directory=link_kind == "directory")
        except OSError:
            pytest.skip("此环境不能创建符号链接")
    analysis = analyze_project(project)
    assert analysis.has_tests is False
    assert "test_external.py" not in analysis.directory_tree
    assert "test_link.py" not in analysis.directory_tree


@pytest.mark.parametrize(
    "filename",
    ["test_app.py", "src/module/test_core.py", "tests/core.py", "src/test/java/example/ApplicationTests.java"],
)
def test_real_project_test_files_are_detected(tmp_path, filename):
    """项目内正常测试仍可识别。"""
    path = tmp_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    assert analyze_project(tmp_path).has_tests is True


@pytest.mark.parametrize(
    "artifact", ["junit:junit", "org.junit.jupiter:junit-jupiter", "org.junit.jupiter:junit-jupiter-api"]
)
def test_declared_junit_dependency_is_test_evidence(tmp_path, artifact):
    """完整 JUnit 坐标是实际声明，单有 Maven 项目不是证据。"""
    group, name = artifact.split(":")
    (tmp_path / "Main.java").write_text("class Main {}", encoding="utf-8")
    (tmp_path / "pom.xml").write_text(
        f"<project><dependencies><dependency><groupId>{group}</groupId><artifactId>{name}</artifactId>"
        "<version>5.10.0</version><scope>test</scope></dependency></dependencies></project>",
        encoding="utf-8",
    )
    assert analyze_project(tmp_path).has_tests is True


def test_maven_defaults_do_not_prove_project_tests(tmp_path):
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    assert analyze_project(tmp_path).has_tests is False
