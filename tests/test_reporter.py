"""报告模块测试"""

from unittest.mock import MagicMock

from rich.console import Console

from repoize.analyzer.project_analyzer import ProjectAnalysis
from repoize.analyzer.quality_analyzer import CodeQualityMetrics
from repoize.reporter.health_report import print_health_report


def create_mock_analysis(
    project_name="test-project",
    primary_language="Python",
    agent_ready_score=80,
    code_quality_score=75,
    has_tests=True,
    has_ci=True,
):
    """创建模拟的项目分析结果。"""
    analysis = MagicMock(spec=ProjectAnalysis)
    analysis.project_name = project_name
    analysis.primary_language = primary_language
    analysis.languages = {"Python": 0.9, "JavaScript": 0.1}
    analysis.profile = MagicMock()
    analysis.profile.name = "Python"
    analysis.frameworks = ["pytest"]
    analysis.dependencies = []
    analysis.commands = MagicMock()
    analysis.commands.test = ["pytest"]
    analysis.commands.lint = ["ruff check ."]
    analysis.commands.format = ["ruff format ."]
    analysis.existing_configs = []
    analysis.env_info = MagicMock()
    analysis.env_info.tools = [("Python", "3.13.5"), ("Node.js", "v24.14.1")]
    analysis.has_tests = has_tests
    analysis.test_framework = "pytest" if has_tests else None
    analysis.has_ci = has_ci
    analysis.agent_ready_score = agent_ready_score
    analysis.agent_ready_label = (
        "完备" if agent_ready_score >= 80 else "部分就绪" if agent_ready_score >= 40 else "未配置"
    )
    analysis.code_quality_score = code_quality_score
    analysis.code_quality_label = "优秀" if code_quality_score >= 80 else "良好" if code_quality_score >= 60 else "一般"
    analysis.quality_metrics = CodeQualityMetrics(
        total_files=38,
        total_lines=3559,
        code_lines=2836,
        comment_lines=110,
        blank_lines=613,
        quality_tools_found=["ruff", "mypy"],
        quality_config_found=["pyproject.toml"],
    )
    return analysis


def test_print_health_report_basic():
    """测试基本健康报告输出。"""
    analysis = create_mock_analysis()
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "📊 项目健康度报告" in output
    assert "test-project" in output
    assert "Python" in output


def test_print_health_report_agent_ready():
    """测试 Agent 就绪度显示。"""
    analysis = create_mock_analysis(agent_ready_score=90)
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "完备" in output
    assert "90/100" in output


def test_print_health_report_code_quality():
    """测试代码质量显示。"""
    analysis = create_mock_analysis(code_quality_score=85)
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "工程配置参考" in output
    assert "85/100" in output
    assert "优秀" not in output
    assert "85/100" in output


def test_print_health_report_with_tests():
    """测试有测试配置的情况。"""
    analysis = create_mock_analysis(has_tests=True)
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "✅ 检测到" in output
    assert "pytest" in output


def test_print_health_report_without_tests():
    """测试无测试配置的情况。"""
    analysis = create_mock_analysis(has_tests=False)
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "❌ 未检测到测试配置" in output


def test_print_health_report_with_ci():
    """测试有 CI 配置的情况。"""
    analysis = create_mock_analysis(has_ci=True)
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "✅ 已配置" in output


def test_print_health_report_without_ci():
    """测试无 CI 配置的情况。"""
    analysis = create_mock_analysis(has_ci=False)
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "⚠️  未检测到" in output


def test_print_health_report_quality_metrics():
    """测试代码质量指标显示。"""
    analysis = create_mock_analysis()
    console = Console(record=True)

    print_health_report(analysis, console)

    output = console.export_text()
    assert "代码统计" in output
    assert "文件数" in output
    assert "总行数" in output
    assert "代码行" in output
    assert "质量工具" in output
    assert "质量配置" in output
