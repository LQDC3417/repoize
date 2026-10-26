"""CLI 入口 — click 命令组"""

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from .analyzer.project_analyzer import ProjectAnalysis, analyze_project
from .changes import FileChange, change_report
from .reporter.health_report import print_health_report
from .targets import GENERATOR_MAP, OUTPUT_PATHS, TYPE_ALIASES, normalize_types, safe_output_path

console = Console()
error_console = Console(stderr=True)
SCHEMA_PATH = Path(__file__).parent / "schemas" / "analysis.schema.json"


def _load_generator(name: str, analysis: ProjectAnalysis, lang: str = "en") -> Any:
    """动态加载生成器类。

    Args:
        name: 生成器名称，必须是 GENERATOR_MAP 中的键
        analysis: 项目分析结果

    Returns:
        生成器实例
    """
    import importlib

    module_path, class_name = GENERATOR_MAP[normalize_types((name,))[0]]
    module = importlib.import_module(f"repoize.{module_path}")
    cls = getattr(module, class_name)
    return cls(analysis, lang=lang)


def _change_options(function):
    """写入命令共用只读预览选项。"""
    for option in (
        click.option("--dry-run", is_flag=True, help="Preview changes without writing files or creating directories."),
        click.option(
            "--format",
            "output_format",
            default="terminal",
            type=click.Choice(["terminal", "json"]),
            help="Output format.",
        ),
        click.option(
            "--diff", "show_diff", is_flag=True, help="Show text differences; requires --dry-run and terminal format."
        ),
    ):
        function = option(function)
    return function


def _run_changes(path, file_types, lang, force, mode, dry_run, output_format, show_diff, check_only=False):
    """一次分析、一次候选计算；检查、预览和应用共享同一结果。"""
    if show_diff and (not dry_run or output_format == "json"):
        raise click.UsageError("--diff requires --dry-run and --format terminal")
    if check_only and dry_run:
        raise click.UsageError("--check and --dry-run are mutually exclusive")
    root = Path(path).absolute()
    changes = []
    try:
        analysis = analyze_project(root, scan_env=False)
    except (OSError, ValueError, RuntimeError, RecursionError):
        analysis = None
    selected = normalize_types(file_types) if file_types else tuple(GENERATOR_MAP)
    for kind in selected:
        if analysis is None:
            changes.append(FileChange(kind, OUTPUT_PATHS[kind], "error", "analysis_failed"))
            continue
        gen = _load_generator(kind, analysis, lang)
        try:
            safe_output_path(root, gen.output_filename)
        except (OSError, ValueError, RuntimeError):
            changes.append(FileChange(kind, gen.output_filename, "error", "invalid_path"))
            continue
        try:
            change = gen.plan(root, mode=mode, force=force)
        except FileNotFoundError:
            if mode == "update" and not file_types:
                continue
            change = FileChange(kind, gen.output_filename, "error", "missing_target")
        except (OSError, ValueError, RuntimeError, RecursionError) as error:
            conflict = isinstance(error, ValueError) and "marker" in str(error)
            change = FileChange(
                kind,
                gen.output_filename,
                "conflict" if conflict else "error",
                "managed_conflict" if conflict else ("migration_required" if "迁移" in str(error) else "invalid_file"),
            )
        change.type = kind
        if check_only and kind == "mcp" and change.action not in {"error", "conflict"}:
            change.action, change.reason = "skip", "not_comparable"
        changes.append(change)
    if not dry_run and not check_only:
        for change in changes:
            if change.action not in {"create", "update", "unchanged"}:
                continue
            try:
                change.apply(root)
            except (OSError, ValueError, RuntimeError):
                change.action, change.reason = "error", "apply_failed"
    report_mode = "check" if check_only else ("dry-run" if dry_run else "apply")
    report = change_report(report_mode, changes)
    for change in changes:
        if change.warning:
            click.echo("WARNING Legacy MCP configuration coexists; manual migration required.", err=True)
    if output_format == "json":
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for change in changes:
            click.echo(
                f"{change.action.upper()} {change.path}: {change.reason}", err=change.action in {"error", "conflict"}
            )
            if change.reason == "missing_target":
                click.echo(f"Run repoize generate --type {change.type} first.", err=True)
            if show_diff:
                difference = change.diff()
                if difference:
                    click.echo(difference)
        click.echo(
            f"Changes: {len(changes)} target(s), {report['summary']['error']} error(s), {report['summary']['conflict']} conflict(s)."
        )
    errors = [change for change in changes if change.action == "error"]
    conflicts = any(change.action == "conflict" for change in changes)
    if check_only:
        if any(change.reason == "invalid_path" for change in errors):
            raise click.exceptions.Exit(2)
        if errors:
            raise click.exceptions.Exit(3)
        if conflicts or any(change.comparable and change.action == "update" for change in changes):
            raise click.exceptions.Exit(1)
        if not any(change.comparable for change in changes):
            raise click.exceptions.Exit(3)
    elif errors or conflicts:
        raise click.exceptions.Exit(1)


@click.group()
@click.version_option(package_name="repoize")
def main() -> None:
    """repoize — Generate evidence-based instructions for AI coding agents."""
    pass


@main.command(help="Create AGENTS.md, plus any explicitly selected client configurations.")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "file_types",
    multiple=True,
    type=click.Choice([*GENERATOR_MAP, *TYPE_ALIASES]),
    help="Add a configuration type; repeat to select several.",
)
@click.option(
    "--lang", default="en", type=click.Choice(["en", "zh"]), show_default=True, help="Language of generated content."
)
@click.option("--force", is_flag=True, help="Replace selected existing configurations.")
@click.option("--no-env", is_flag=True, help="Compatibility option; environment scanning is off by default.")
@_change_options
def init(path, file_types, lang, force, no_env, dry_run, output_format, show_diff):
    """默认仅生成 AGENTS.md，显式类型追加到默认目标。"""
    _run_changes(path, normalize_types(("agents", *file_types)), lang, force, "init", dry_run, output_format, show_diff)


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


@main.command(help="Generate only the explicitly selected configuration types.")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "file_types",
    multiple=True,
    type=click.Choice([*GENERATOR_MAP, *TYPE_ALIASES]),
    help="Configuration type to generate; repeat to select several.",
)
@click.option(
    "--lang", default="en", type=click.Choice(["en", "zh"]), show_default=True, help="Language of generated content."
)
@click.option("--force", is_flag=True, help="Replace selected existing configurations.")
@click.option("--no-env", is_flag=True, help="Compatibility option; environment scanning is off by default.")
@_change_options
def generate(path, file_types, lang, force, no_env, dry_run, output_format, show_diff):
    """选择性生成指定类型的配置文件。"""
    if not file_types:
        click.echo("Select at least one configuration type with --type.", err=True)
        raise click.exceptions.Exit(1)
    _run_changes(path, file_types, lang, force, "generate", dry_run, output_format, show_diff)


@main.command(help="Update existing supported targets while preserving handwritten content.")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "file_types",
    multiple=True,
    type=click.Choice([*GENERATOR_MAP, *TYPE_ALIASES]),
    help="Configuration type to update; repeat to select several.",
)
@click.option("--no-env", is_flag=True, help="Compatibility option; environment scanning is off by default.")
@click.option(
    "--lang", default="en", type=click.Choice(["en", "zh"]), show_default=True, help="Language of generated content."
)
@click.option(
    "--check", "check_only", is_flag=True, help="Check managed text drift without writing; MCP is not comparable."
)
@_change_options
def update(path, file_types, lang, no_env, check_only, dry_run, output_format, show_diff):
    """增量更新已生成配置，保留手写内容。"""
    _run_changes(path, file_types, lang, False, "update", dry_run, output_format, show_diff, check_only)


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
        console.print("[bold red]🚀 建议运行 'repoize init' 生成 AGENTS.md；通过 --type 添加客户端配置。[/bold red]")


@main.command(help="Check local configuration formats and command evidence without executing project commands.")
@click.argument("path", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--type",
    "file_types",
    multiple=True,
    type=click.Choice([*GENERATOR_MAP, *TYPE_ALIASES]),
    help="Check only these configuration types; repeat to select several.",
)
@click.option(
    "--format", "output_format", default="terminal", type=click.Choice(["terminal", "json"]), help="Output format."
)
@click.option("--strict", is_flag=True, help="Fail on warnings as well as errors.")
def doctor(path: str, file_types: tuple[str, ...], output_format: str, strict: bool) -> None:
    """只读检查项目配置及命令证据。"""
    from .doctor import diagnose_project
    from .targets import safe_project_entry

    project_path = Path(path).absolute()
    try:
        if not safe_project_entry(project_path, project_path, strict=True):
            raise click.BadParameter(
                "Project path must be a regular directory without links or reparse points.", param_hint="path"
            )
        report = diagnose_project(project_path, file_types)
    except (OSError, RuntimeError):
        click.echo("Doctor could not complete the local inspection (runtime or filesystem error).", err=True)
        raise click.exceptions.Exit(3) from None
    if output_format == "json":
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for finding in report["findings"]:
            click.echo(
                f"{finding['severity'].upper()} {finding['rule_id']} type={finding['type'] or 'project'} {finding['path'] or '-'}: {finding['message']}"
            )
            click.echo(f"  Evidence: {'; '.join(finding['evidence']) or '(none)'}")
            click.echo(f"  Fix: {finding['suggestion']}")
        if report["command_evidence"]:
            click.echo("Command evidence:")
            for command in report["command_evidence"]:
                click.echo(f"  {command['category']}: {command['command']} (verification={command['verification']})")
                for source in command["sources"]:
                    click.echo(
                        f"    kind={source['kind']} path={source['path'] or '-'} selector={source['selector'] or '-'}"
                    )
        counts = report["summary"]
        click.echo(
            f"Checked {counts['checked_files']} configuration file(s): {counts['errors']} error(s), {counts['warnings']} warning(s)."
        )
        click.echo("Local formats only; client loading, command execution, and network access were not checked.")
    if report["summary"]["errors"] or (strict and report["summary"]["warnings"]):
        raise click.exceptions.Exit(1)


if __name__ == "__main__":
    main()
