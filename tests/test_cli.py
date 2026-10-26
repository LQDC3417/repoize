"""CLI 模块测试"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from repoize.cli import main


@pytest.fixture
def runner():
    """创建 CLI 测试运行器。"""
    return CliRunner()


@pytest.fixture
def sample_project(tmp_path):
    """创建示例项目目录。"""
    # 创建一个简单的 Python 项目
    (tmp_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
""")
    (tmp_path / "main.py").write_text("print('Hello, World!')")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_hello(): pass")
    return tmp_path


def test_main_help(runner):
    """测试主命令帮助信息。"""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "repoize" in result.output
    assert "一条命令让任何项目对 AI Agent 友好" in result.output


def test_analyze_help(runner):
    """测试 analyze 命令帮助信息。"""
    result = runner.invoke(main, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "分析项目结构" in result.output


def test_generate_help(runner):
    """测试 generate 命令帮助信息。"""
    result = runner.invoke(main, ["generate", "--help"])
    assert result.exit_code == 0
    assert "选择性生成指定类型的配置文件" in result.output


def test_check_help(runner):
    """测试 check 命令帮助信息。"""
    result = runner.invoke(main, ["check", "--help"])
    assert result.exit_code == 0
    assert "检查项目是否已具备 Agent 友好配置" in result.output


def test_validate_help(runner):
    """测试 validate 命令帮助信息。"""
    result = runner.invoke(main, ["validate", "--help"])
    assert result.exit_code == 0
    assert "校验" in result.output


def test_analyze_json_output(runner, sample_project):
    """测试 analyze 命令 JSON 输出。"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        output_file = f.name

    try:
        result = runner.invoke(
            main, ["analyze", str(sample_project), "--format", "json", "--output", output_file, "--no-env"]
        )
        assert result.exit_code == 0
        assert "✅ 已写入" in result.output

        # 验证输出文件存在
        assert Path(output_file).exists()
    finally:
        Path(output_file).unlink(missing_ok=True)


def test_analyze_terminal_output(runner, sample_project):
    """测试 analyze 命令终端输出。"""
    result = runner.invoke(main, ["analyze", str(sample_project), "--format", "terminal", "--no-env"])
    assert result.exit_code == 0
    assert "📊 项目健康度报告" in result.output


def test_generate_missing_types(runner, sample_project):
    """测试 generate 命令缺少类型参数。"""
    result = runner.invoke(main, ["generate", str(sample_project)])
    assert result.exit_code == 1
    assert "请至少指定一个文件类型" in result.output


def test_generate_with_type(runner, sample_project):
    """测试 generate 命令指定类型。"""
    result = runner.invoke(main, ["generate", str(sample_project), "--type", "agents", "--no-env"])
    assert result.exit_code == 0
    assert "✅ 生成 AGENTS.md" in result.output


def test_check_command(runner, sample_project):
    """测试 check 命令。"""
    result = runner.invoke(main, ["check", str(sample_project)])
    assert result.exit_code == 0
    assert "📊 项目健康度报告" in result.output


def test_analyze_json_stdout_is_machine_readable(runner, sample_project):
    """JSON 不混入状态文字，长路径和方括号保持原样。"""
    project = sample_project / ("demo[bold]" + "x" * 90)
    project.mkdir()
    (project / "main.py").write_text("pass", encoding="utf-8")

    result = runner.invoke(main, ["analyze", str(project), "--format", "json", "--no-env"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["project_name"] == project.name
    assert data["project_path"] == str(project.resolve())
    assert "正在分析项目" in result.stderr


def test_analyze_json_file_leaves_stdout_empty(runner, sample_project, tmp_path):
    """写入 JSON 文件时，全部状态信息发送到 stderr。"""
    output = tmp_path / "report.json"

    result = runner.invoke(
        main, ["analyze", str(sample_project), "--format", "json", "--output", str(output), "--no-env"]
    )

    assert result.exit_code == 0
    assert result.stdout == ""
    assert json.loads(output.read_text(encoding="utf-8-sig"))["project_name"] == sample_project.name
    assert "已写入" in result.stderr


@pytest.mark.parametrize("command", ["init", "generate", "update"])
def test_write_failure_returns_error_and_continues(runner, sample_project, command):
    """一个文件写入失败，不阻止其他文件，但最终返回失败。"""
    (sample_project / "AGENTS.md").mkdir()
    args = [command, str(sample_project), "--no-env"]
    if command in {"init", "generate"}:
        args.append("--force")
    if command != "init":
        args.extend(["--type", "agents", "--type", "claude"])

    result = runner.invoke(main, args)

    assert result.exit_code == 1
    assert "AGENTS.md" in result.stderr
    assert "失败 1" in result.output
    assert (sample_project / "CLAUDE.md").is_file()


def test_update_invalid_json_returns_error_without_overwriting(runner, sample_project):
    """无效 MCP 配置作为失败报告，保留原文件并继续更新。"""
    output = sample_project / ".mcp.json"
    output.write_text("{invalid", encoding="utf-8")

    result = runner.invoke(main, ["update", str(sample_project), "--type", "mcp", "--type", "claude", "--no-env"])

    assert result.exit_code == 1
    assert ".mcp.json" in result.stderr
    assert output.read_text(encoding="utf-8") == "{invalid"
    assert (sample_project / "CLAUDE.md").is_file()


def test_analyze_unavailable_html_returns_error(runner, sample_project):
    """尚未实现的格式不能返回成功。"""
    result = runner.invoke(main, ["analyze", str(sample_project), "--format", "html", "--no-env"])

    assert result.exit_code != 0
    assert "HTML 格式暂不支持" in result.output


def test_analyze_json_write_failure_is_reported(runner, sample_project):
    """JSON 输出路径不可写时，返回清晰错误及非零状态。"""
    blocker = sample_project / "blocked"
    blocker.write_text("occupied", encoding="utf-8")

    result = runner.invoke(
        main,
        ["analyze", str(sample_project), "--format", "json", "--output", str(blocker / "report.json"), "--no-env"],
    )

    assert result.exit_code == 1
    assert "失败" in result.stderr
