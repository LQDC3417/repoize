"""项目健康度报告生成器"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..analyzer.project_analyzer import ProjectAnalysis


def print_health_report(analysis: ProjectAnalysis, console: Console | None = None) -> None:
    """输出终端格式的健康度报告。"""
    if console is None:
        console = Console()

    # 标题
    console.print()
    console.print(
        Panel(
            f"[bold]{analysis.project_name}[/bold]",
            title="📊 项目健康度报告",
            border_style="blue",
        )
    )

    # 语言信息
    if analysis.languages:
        lang_text = Text()
        for i, (lang, ratio) in enumerate(analysis.languages.items()):
            if i > 0:
                lang_text.append(" | ")
            label = "主" if i == 0 else f"{ratio:.0%}"
            lang_text.append(f"{lang} ({label})", style="bold green" if i == 0 else "dim")
        console.print("\n[bold]语言:[/bold] ", end="")
        console.print(lang_text)

    if analysis.profile:
        console.print(f"\n[bold]语言画像:[/bold] {analysis.profile.name}")
    if analysis.frameworks:
        console.print(f"[bold]框架:[/bold] {', '.join(analysis.frameworks)}")

    # 框架/依赖
    main_deps = [d for d in analysis.dependencies if not d.dev]
    if main_deps:
        console.print(f"[bold]依赖:[/bold] {', '.join(d.name for d in main_deps[:10])}")
        if len(main_deps) > 10:
            console.print(f"  ...及其他 {len(main_deps) - 10} 个")

    # Agent 就绪度
    score = analysis.agent_ready_score
    label = analysis.agent_ready_label
    if score >= 80:
        style = "green"
    elif score >= 40:
        style = "yellow"
    else:
        style = "red"

    console.print(f"\n[bold]配置覆盖参考:[/bold] [{style}]{label} ({score}/100)[/{style}]")

    # 代码质量评分
    quality_score = analysis.code_quality_score
    if quality_score >= 80:
        quality_style = "green"
    elif quality_score >= 60:
        quality_style = "yellow"
    else:
        quality_style = "red"

    console.print(f"[bold]工程配置参考:[/bold] [{quality_style}]{quality_score}/100[/{quality_style}]")
    console.print("[dim]以上分数仅供参考，不验证格式有效性、代码质量或客户端加载情况。[/dim]")

    # 配置文件状态表
    table = Table(show_header=True, header_style="bold")
    table.add_column("配置文件", style="cyan")
    table.add_column("状态", justify="center")
    table.add_column("说明")

    config_desc = {
        "agents_md": "通用 Agent 指令",
        "claude_md": "Claude Code 专属指令",
        "cursorrules": "Cursor AI 规则",
        "copilot": "GitHub Copilot 指令",
        "claude_code": "Claude Code 设置",
        "mcp_claude": "Claude MCP 配置",
        "mcp_desktop": "Claude Desktop MCP",
        "mcp_generic": "通用 MCP 配置",
        "skill": "项目 Skill 文件",
        "skill_claude": "Claude Skill 文件",
        "windsurf": "Windsurf 规则",
        "cline": "Cline 规则",
    }

    for cfg in analysis.existing_configs:
        status = "[green]✅ 已配置[/green]" if cfg.exists else "[red]❌ 未配置[/red]"
        desc = config_desc.get(cfg.config_type, "")
        table.add_row(cfg.name, status, desc)

    console.print()
    console.print(table)

    # 代码质量详情
    if analysis.quality_metrics.total_files > 0:
        console.print("\n[bold]代码统计:[/bold]")
        console.print(f"  文件数: [cyan]{analysis.quality_metrics.total_files}[/cyan]")
        console.print(f"  总行数: [cyan]{analysis.quality_metrics.total_lines:,}[/cyan]")
        console.print(f"  代码行: [cyan]{analysis.quality_metrics.code_lines:,}[/cyan]")
        console.print(f"  注释行: [cyan]{analysis.quality_metrics.comment_lines:,}[/cyan]")
        console.print(f"  空行: [cyan]{analysis.quality_metrics.blank_lines:,}[/cyan]")

        if analysis.quality_metrics.quality_tools_found:
            console.print(f"  质量工具: [green]{', '.join(analysis.quality_metrics.quality_tools_found)}[/green]")

        if analysis.quality_metrics.quality_config_found:
            console.print(f"  质量配置: [green]{', '.join(analysis.quality_metrics.quality_config_found)}[/green]")

    # 开发环境摘要
    if analysis.env_info.tools:
        console.print("\n[bold]开发环境:[/bold]")
        for name, version in analysis.env_info.tools[:8]:
            console.print(f"  {name}: [dim]{version}[/dim]")
        if len(analysis.env_info.tools) > 8:
            console.print(f"  ...及其他 {len(analysis.env_info.tools) - 8} 个工具")

    # 测试信息
    if analysis.has_tests:
        fw = f" ({analysis.test_framework})" if analysis.test_framework else ""
        console.print(f"\n[bold]测试:[/bold] [green]✅ 检测到{fw}[/green]")
    else:
        console.print("\n[bold]测试:[/bold] [red]❌ 未检测到测试配置[/red]")

    # CI 信息
    if analysis.has_ci:
        console.print("[bold]CI/CD:[/bold] [green]✅ 已配置[/green]")
    else:
        console.print("[bold]CI/CD:[/bold] [yellow]⚠️  未检测到[/yellow]")

    # 命令信息
    cmds = analysis.commands
    if cmds.test or cmds.lint or cmds.format:
        console.print("\n[bold]常用命令:[/bold]")
        for cmd in cmds.test[:1]:
            console.print(f"  测试: [cyan]{cmd}[/cyan]")
        for cmd in cmds.lint[:1]:
            console.print(f"  检查: [cyan]{cmd}[/cyan]")
        for cmd in cmds.format[:1]:
            console.print(f"  格式: [cyan]{cmd}[/cyan]")

    console.print()
