"""CLI 入口 — click 命令组"""

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.prompt import Confirm

from .analyzer.project_analyzer import ProjectAnalysis, analyze_project
from .reporter.health_report import print_health_report
from .targets import legacy_decision, safe_output_path

console = Console()
error_console = Console(stderr=True)
SCHEMA_PATH = Path(__file__).parent / "schemas" / "analysis.schema.json"

# 生成器类型到模块的映射
GENERATOR_MAP: dict[str, tuple[str, str]] = {
    "agents": ("generator.agents_md", "AgentsMdGenerator"),
    "claude": ("generator.claude_md", "ClaudeMdGenerator"),
    "cursorrules": ("generator.cursorrules", "CursorRulesGenerator"),
    "copilot": ("generator.copilot", "CopilotGenerator"),
    "mcp": ("generator.mcp_config", "McpConfigGenerator"),
    "skill": ("generator.skill_md", "SkillMdGenerator"),
}


def _load_generator(name: str, analysis: ProjectAnalysis) -> Any:
    """动态加载生成器类。

    Args:
        name: 生成器名称，必须是 GENERATOR_MAP 中的键
        analysis: 项目分析结果

    Returns:
        生成器实例
    """
    import importlib

    module_path, class_name = GENERATOR_MAP[name]
    module = importlib.import_module(f"repoize.{module_path}")
    cls = getattr(module, class_name)
    return cls(analysis)


def _analyze_and_report(project_path: Path, scan_env: bool) -> ProjectAnalysis:
    """分析项目并打印健康报告。

    Args:
        project_path: 项目根目录路径
        scan_env: 是否扫描环境变量

    Returns:
        项目分析结果
    """
    if scan_env:
        console.print("[dim]📡 扫描开发环境...[/dim]")

    analysis = analyze_project(project_path, scan_env=scan_env)
    print_health_report(analysis, console)
    return analysis


def _check_existing_configs(analysis: ProjectAnalysis, force: bool) -> bool:
    """检查已有配置文件，如果需要确认则返回 True 表示继续。

    Args:
        analysis: 项目分析结果
        force: 是否强制覆盖

    Returns:
        True 表示继续执行，False 表示取消
    """
    # 迁移或安全错误必须按类型汇总，不能被交互确认掩盖。
    for gen_name in GENERATOR_MAP:
        gen = _load_generator(gen_name, analysis)
        try:
            output = safe_output_path(analysis.project_path, gen.output_filename)
            if legacy_decision(analysis.project_path, gen.output_filename):
                return True
            gen.validate_existing(output)
        except (OSError, ValueError):
            return True
    existing = [c for c in analysis.existing_configs if c.exists]
    if existing and not force:
        console.print(f"[yellow]⚠️  检测到 {len(existing)} 个已有配置文件。[/yellow]")
        for c in existing:
            console.print(f"  - {c.name}")
        if not Confirm.ask("是否继续？已有文件将被跳过"):
            console.print("[dim]已取消。[/dim]")
            return False
    return True


def _generate_all_configs(
    project_path: Path, analysis: ProjectAnalysis, force: bool, file_types: tuple[str, ...] = ()
) -> tuple[list[str], list[str], list[str]]:
    """生成所有或指定的配置文件。

    Args:
        project_path: 项目根目录路径
        analysis: 项目分析结果
        force: 是否强制覆盖
        file_types: 要生成的类型，空值表示全部

    Returns:
        (生成的文件列表, 跳过的文件列表, 失败的文件列表)
    """
    console.print("\n[bold]⚙️  开始生成配置文件...[/bold]\n")
    generated: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for gen_name in file_types or tuple(GENERATOR_MAP):
        gen = _load_generator(gen_name, analysis)
        try:
            output_path = safe_output_path(project_path, gen.output_filename)
            warning = legacy_decision(project_path, gen.output_filename)
            if warning:
                error_console.print(f"  [yellow]⚠️  {warning}[/yellow]")
            gen.validate_existing(output_path)
            if output_path.exists() and not force:
                skipped.append(gen.output_filename)
                console.print(f"  [yellow]⏭  跳过 {gen.output_filename}（已存在）[/yellow]")
                continue
            gen.write(project_path, force=force)
            generated.append(gen.output_filename)
            console.print(f"  [green]✅ 生成 {gen.output_filename}[/green]")
        except (OSError, ValueError) as e:
            failed.append(gen.output_filename)
            error_console.print(f"  [red]❌ 生成 {gen.output_filename} 失败: {e}[/red]")

    return generated, skipped, failed


def _print_generation_summary(generated: list[str], skipped: list[str], failed: list[str]) -> None:
    """打印生成结果汇总。

    Args:
        generated: 生成的文件列表
        skipped: 跳过的文件列表
        failed: 失败的文件列表
    """
    if failed:
        error_console.print(f"\n[bold red]❌ 生成 {len(generated)} 个文件，失败 {len(failed)} 个[/bold red]")
    else:
        console.print(f"\n[bold green]✅ 完成！生成 {len(generated)} 个文件[/bold green]")
    if skipped:
        console.print(f"[yellow]⏭  跳过 {len(skipped)} 个已存在文件（使用 --force 覆盖）[/yellow]")
    if failed:
        raise click.exceptions.Exit(1)


@click.group()
@click.version_option(package_name="repoize")
def main() -> None:
    """repoize — 一条命令让任何项目对 AI Agent 友好。

    自动生成 AGENTS.md、CLAUDE.md、Cursor .mdc 规则、MCP 配置、Skill 文件，
    让 Claude Code、Cursor、Copilot 等 AI 编程助手立即理解你的项目。
    """
    pass


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--force", is_flag=True, help="覆盖已有配置文件")
@click.option("--no-env", is_flag=True, help="跳过环境变量扫描")
def init(path: str, force: bool, no_env: bool) -> None:
    """扫描项目并一键生成所有 Agent 配置文件。"""
    project_path = Path(path).absolute()
    console.print(f"[bold blue]🔍 正在扫描项目:[/bold blue] {project_path}")

    # 分析项目并打印报告
    analysis = _analyze_and_report(project_path, scan_env=False)

    # 检查已有配置
    if not _check_existing_configs(analysis, force):
        return

    # 生成所有配置文件
    generated, skipped, failed = _generate_all_configs(project_path, analysis, force)

    # 打印汇总
    _print_generation_summary(generated, skipped, failed)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--format",
    "output_format",
    default="terminal",
    type=click.Choice(["terminal", "json", "html"]),
    help="输出格式",
)
@click.option("--output", "output_file", type=click.Path(dir_okay=False), default=None, help="JSON 输出文件路径")
@click.option("--no-env", is_flag=True, help="跳过环境变量扫描")
@click.option("--include-env", is_flag=True, help="仅收集平台与工具版本，不收集环境变量值")
def analyze(path: str, output_format: str, output_file: str | None, no_env: bool, include_env: bool) -> None:
    """分析项目结构并输出健康度报告（不生成文件）。"""
    if include_env and no_env:
        raise click.UsageError("--include-env 与 --no-env 不能同时使用")
    if output_format == "html":
        raise click.BadParameter("HTML 格式暂不支持，请使用 terminal 或 json", param_hint="--format")

    project_path = Path(path).resolve()
    status_console = error_console if output_format == "json" else console
    status_console.print(f"[bold blue]📊 正在分析项目:[/bold blue] {project_path}")

    analysis = analyze_project(project_path, scan_env=include_env)

    if output_format == "json":
        payload = json.dumps(analysis.to_dict(), ensure_ascii=False, indent=2)
        if output_file:
            output_path = Path(output_file)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(payload + "\n", encoding="utf-8-sig")
            except OSError as e:
                raise click.ClickException(f"写入 JSON 文件失败: {output_path}: {e}") from e
            error_console.print(f"[green]✅ 已写入 {output_path}[/green]")
        else:
            click.echo(payload)
    else:
        print_health_report(analysis, console)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "file_types",
    multiple=True,
    type=click.Choice(["agents", "claude", "cursorrules", "copilot", "mcp", "skill"]),
    help="要生成的配置文件类型（可多次指定）",
)
@click.option("--force", is_flag=True, help="覆盖已有配置文件")
@click.option("--no-env", is_flag=True, help="跳过环境变量扫描")
def generate(path: str, file_types: tuple[str, ...], force: bool, no_env: bool) -> None:
    """选择性生成指定类型的配置文件。"""
    if not file_types:
        console.print("[red]请至少指定一个文件类型，例如: --type agents --type mcp[/red]")
        console.print("\n可用类型:")
        for name in GENERATOR_MAP:
            console.print(f"  - {name}")
        raise SystemExit(1)

    project_path = Path(path).absolute()
    console.print(f"[bold blue]⚙️  正在生成配置:[/bold blue] {', '.join(file_types)}")

    analysis = analyze_project(project_path, scan_env=False)

    generated, skipped, failed = _generate_all_configs(project_path, analysis, force, file_types)
    _print_generation_summary(generated, skipped, failed)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "file_types",
    multiple=True,
    type=click.Choice(["agents", "claude", "cursorrules", "copilot", "mcp", "skill"]),
    help="要更新的配置文件类型（可多次指定）",
)
@click.option("--no-env", is_flag=True, help="跳过环境变量扫描")
def update(path: str, file_types: tuple[str, ...], no_env: bool) -> None:
    """增量更新已生成配置，保留手写内容。"""
    project_path = Path(path).absolute()
    console.print(f"[bold blue]🔄 正在更新配置:[/bold blue] {project_path}")

    analysis = analyze_project(project_path, scan_env=False)
    selected_types = file_types or tuple(GENERATOR_MAP)
    updated: list[str] = []
    created: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for gen_name in selected_types:
        gen = _load_generator(gen_name, analysis)
        output_path = project_path / gen.output_filename

        try:
            output_path = safe_output_path(project_path, gen.output_filename)
            warning = legacy_decision(project_path, gen.output_filename)
            if warning:
                error_console.print(f"  [yellow]⚠️  {warning}[/yellow]")
            if not output_path.exists():
                gen.write(project_path, force=True)
                created.append(gen.output_filename)
                console.print(f"  [green]✅ 创建 {gen.output_filename}[/green]")
                continue

            result = gen.update(project_path)
            if result is None:
                skipped.append(gen.output_filename)
                console.print(f"  [yellow]⏭  跳过 {gen.output_filename}（无 managed marker）[/yellow]")
            else:
                updated.append(gen.output_filename)
                console.print(f"  [green]✅ 更新 {gen.output_filename}[/green]")
        except (OSError, ValueError) as e:
            failed.append(gen.output_filename)
            error_console.print(f"  [red]❌ 更新 {gen.output_filename} 失败: {e}[/red]")

    if failed:
        error_console.print(
            f"\n[bold red]❌ 更新 {len(updated)} 个，创建 {len(created)} 个文件，失败 {len(failed)} 个[/bold red]"
        )
    else:
        console.print(f"\n[bold green]✅ 完成！更新 {len(updated)} 个，创建 {len(created)} 个文件[/bold green]")
    if skipped:
        console.print(f"[yellow]⏭  跳过 {len(skipped)} 个未管理的已有文件[/yellow]")
    if failed:
        raise click.exceptions.Exit(1)


@main.command()
@click.argument("json_file", type=click.Path(exists=True, dir_okay=False))
def validate(json_file: str) -> None:
    """校验 analyze --format json 输出是否符合 JSON Schema。"""
    import jsonschema

    json_path = Path(json_file)
    try:
        data = json.loads(json_path.read_text(encoding="utf-8-sig"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
        jsonschema.validate(data, schema)
    except (OSError, UnicodeDecodeError, ValueError, jsonschema.ValidationError) as e:
        console.print(f"[red]❌ JSON 校验失败: {e}[/red]")
        raise SystemExit(1) from e

    console.print("[green]✅ JSON 校验通过[/green]")


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
def check(path: str) -> None:
    """检查项目是否已具备 Agent 友好配置。"""
    project_path = Path(path).resolve()
    console.print(f"[bold blue]✅ 正在检查项目:[/bold blue] {project_path}")

    analysis = analyze_project(project_path)
    print_health_report(analysis, console)

    # 给出建议
    score = analysis.agent_ready_score
    if score >= 80:
        console.print("[bold green]配置覆盖较完整；分数不代表格式有效或客户端可加载。[/bold green]")
    elif score >= 40:
        console.print("[bold yellow]💡 建议运行 'repoize init' 补充缺失的配置文件。[/bold yellow]")
    else:
        console.print("[bold red]🚀 建议运行 'repoize init' 一键生成所有配置文件。[/bold red]")


if __name__ == "__main__":
    main()
