"""轻量只读诊断：只校验项目声明和配置，不启动命令或扫描运行环境。"""

import json
import re
from pathlib import Path

from .analyzer.cmd_extractor import extract_commands
from .analyzer.config_scanner import scan_existing_configs
from .analyzer.lang_detector import get_primary_language
from .analyzer.language_profiles import get_language_profile
from .formats import marker_bounds, split_frontmatter
from .targets import GENERATOR_MAP, normalize_types, safe_project_entry

DOCTOR_TYPES = tuple(GENERATOR_MAP)
_CONFIG_TYPES = {
    "agents_md": "agents",
    "claude_md": "claude",
    "cursorrules": "cursor",
    "copilot": "copilot",
    "mcp_claude": "mcp",
    "mcp_generic": "mcp",
    "mcp_desktop": "mcp",
    "skill": "skill",
    "skill_claude": "skill",
}
_LEGACY = {".cursorrules", ".claude/mcp.json"}


def _finding(
    rule_id: str,
    severity: str,
    config_type: str | None,
    path: str | None,
    message: str,
    suggestion: str,
    evidence: list[str] | None = None,
) -> dict:
    """诊断证据只含安全类别或位置，不携带配置原文。"""
    return {
        "rule_id": rule_id,
        "severity": severity,
        "type": config_type,
        "path": path,
        "message": message,
        "evidence": evidence or [],
        "suggestion": suggestion,
    }


def _check_config(root: Path, path: Path, config_type: str) -> list[dict]:
    """检查文件本地格式，保留未知字段，不声称客户端可以加载。"""
    relative = path.relative_to(root).as_posix()
    findings = []

    def add(rule_id, severity, message, suggestion, evidence=None):
        findings.append(_finding(rule_id, severity, config_type, relative, message, suggestion, evidence))

    if relative in _LEGACY:
        add(
            "CFG002",
            "warning",
            "Legacy configuration entry; manual migration may be needed.",
            "Review the supported project entry for this client before migrating.",
        )
    try:
        accepted = safe_project_entry(path, root, strict=True)
    except OSError:
        add(
            "CFG003",
            "error",
            "Configuration metadata is unreadable.",
            "Check file permissions and access to parent directories.",
        )
        return findings
    if not accepted:
        add(
            "CFG003",
            "error",
            "Configuration is not a safe project file (link or reparse point).",
            "Use a regular file inside the project.",
        )
        return findings
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        add(
            "CFG003",
            "error",
            "Configuration is unreadable or is not UTF-8.",
            "Check file permissions and UTF-8 encoding.",
        )
        return findings
    if not content.strip():
        add("CFG003", "error", "Configuration is empty.", "Add configuration content.")
        return findings
    if config_type == "mcp":
        try:
            data = json.loads(content)
        except (ValueError, RecursionError):
            add(
                "CFG004",
                "error",
                "Configuration has invalid JSON syntax.",
                "Repair JSON syntax without changing server credentials.",
            )
            return findings
        if not isinstance(data, dict) or not isinstance(data.get("mcpServers", {}), dict):
            add(
                "CFG004",
                "error",
                "MCP root and mcpServers must be objects.",
                "Use an object containing an mcpServers object.",
            )
        elif any(not isinstance(server, dict) for server in data.get("mcpServers", {}).values()):
            add("CFG004", "error", "Each MCP server must be an object.", "Repair server object structure.")
        elif not data.get("mcpServers"):
            add("CFG007", "warning", "No MCP servers are configured.", "Add servers only if your workflow needs them.")
        elif any(not server for server in data["mcpServers"].values()):
            add(
                "CFG007", "warning", "MCP contains an empty server object.", "Configure or remove empty server entries."
            )
        return findings
    bounds = None
    try:
        bounds = marker_bounds(content)
    except ValueError:
        add(
            "UPD001",
            "error",
            "Managed markers are incomplete, duplicated, or out of order.",
            "Keep one complete ordered marker pair, or remove both markers.",
        )
    if path.name == "SKILL.md" or path.suffix == ".mdc":
        try:
            header, _ = split_frontmatter(content, str(path))
        except (ValueError, RecursionError) as error:
            reason = str(error) if isinstance(error, ValueError) else "YAML"
            rule_id = (
                "CFG004"
                if "YAML" in reason or "frontmatter 必须是对象" in reason
                else ("CFG005" if config_type == "skill" else "CFG006")
            )
            location = re.search(r"行 (\d+)，列 (\d+)", reason)
            evidence = [f"line {location[1]}, column {location[2]}"] if location else []
            add(
                rule_id,
                "error",
                "Invalid frontmatter syntax, structure, or metadata.",
                "Review Skill name/directory/description or Cursor field types and YAML syntax.",
                evidence,
            )
        else:
            if bounds and bounds[0] < len(header):
                add(
                    "UPD001",
                    "error",
                    "Managed markers overlap frontmatter.",
                    "Place the complete marker pair after frontmatter.",
                )
    return findings


def diagnose_project(project_path: Path, file_types: tuple[str, ...] = ()) -> dict:
    """返回独立 doctor v1 报告；显式选择只要求所选工具的入口。"""
    root = Path(project_path).absolute()
    canonical = set(normalize_types(file_types))
    if not canonical.issubset(DOCTOR_TYPES):
        raise ValueError("Unsupported diagnostic type.")
    configs = [
        config
        for config in scan_existing_configs(root, strict=True)
        if config.exists and config.config_type in _CONFIG_TYPES
    ]
    discovered = {_CONFIG_TYPES[config.config_type] for config in configs}
    selected = sorted(canonical or discovered)
    findings = []
    for config_type in sorted(canonical - discovered):
        findings.append(
            _finding(
                "CFG001",
                "error",
                config_type,
                None,
                "Explicitly selected configuration entry is missing.",
                "Create an entry for the selected client if you intend to use it.",
            )
        )
    if not file_types and not configs:
        findings.append(
            _finding(
                "CFG001",
                "warning",
                None,
                None,
                "No supported project configuration was found.",
                "Select a client you use and create its project configuration.",
            )
        )
    checked = 0
    for config in sorted(configs, key=lambda config: config.path.relative_to(root).as_posix()):
        config_type = _CONFIG_TYPES[config.config_type]
        if config_type in selected:
            findings.extend(_check_config(root, config.path, config_type))
            checked += 1
    commands = extract_commands(root, get_language_profile(get_primary_language(root, strict=True)))
    findings.extend(commands.issues)
    for item in commands.evidence:
        if all(source.kind == "suggested" for source in item.sources):
            findings.append(
                _finding(
                    "CMD001",
                    "info",
                    None,
                    None,
                    "Command has only default suggestions and was not executed.",
                    "Verify the project declaration before using this command.",
                    [f"{item.category}: {item.command}"],
                )
            )
    findings.sort(
        key=lambda item: (item["path"] or "", item["type"] or "", item["rule_id"], item["message"], item["evidence"])
    )
    return {
        "report_type": "doctor",
        "schema_version": 1,
        "selected_types": selected,
        "findings": findings,
        "command_evidence": commands.evidence_dict(),
        "summary": {
            "errors": sum(item["severity"] == "error" for item in findings),
            "warnings": sum(item["severity"] == "warning" for item in findings),
            "info": sum(item["severity"] == "info" for item in findings),
            "checked_files": checked,
        },
    }
