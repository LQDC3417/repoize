"""已有 Agent 配置文件扫描器"""

import os
import stat
from pathlib import Path

from ..targets import safe_project_entry
from .lang_detector import IGNORE_DIRS

# 已知的 Agent 配置文件及其类型
AGENT_CONFIGS = {
    "AGENTS.md": "agents_md",
    "CLAUDE.md": "claude_md",
    ".cursorrules": "cursorrules",
    ".github/copilot-instructions.md": "copilot",
    ".claude/settings.json": "claude_code",
    ".claude/mcp.json": "mcp_claude",
    ".mcp.json": "mcp_claude",
    "mcp.json": "mcp_generic",
    "claude_desktop_config.json": "mcp_desktop",
    "SKILL.md": "skill",
    ".windsurfrules": "windsurf",
    ".clinerules": "cline",
}


class ConfigStatus:
    """配置文件状态。"""

    def __init__(self, name: str, config_type: str, exists: bool, path: Path):
        """初始化配置状态。"""
        self.name = name
        self.config_type = config_type
        self.exists = exists
        self.path = path

    def __repr__(self) -> str:
        """返回配置状态的字符串表示。"""
        status = "✅" if self.exists else "❌"
        return f"{status} {self.name}"

    def to_dict(self) -> dict:
        """返回 JSON 可序列化的配置状态。"""
        return {
            "name": self.name,
            "config_type": self.config_type,
            "exists": self.exists,
            "path": str(self.path),
        }


def scan_existing_configs(project_path: Path, *, strict: bool = False) -> list[ConfigStatus]:
    """扫描项目中已有的 Agent 配置文件。"""
    project_path = Path(project_path)
    results: list[ConfigStatus] = []

    for filename, config_type in AGENT_CONFIGS.items():
        filepath = project_path / filename
        results.append(
            ConfigStatus(
                name=filename,
                config_type=config_type,
                exists=_is_config_file(filepath, strict=strict),
                path=filepath,
            )
        )

    # 检查 .claude/ 目录下的 skills
    claude_skills_dir = project_path / ".claude" / "skills"
    if safe_project_entry(claude_skills_dir, project_path, strict=strict) and claude_skills_dir.is_dir():
        for skill_file in _config_files(claude_skills_dir, project_path, strict=strict):
            if skill_file.name != "SKILL.md":
                continue
            if not _is_config_file(skill_file, strict=strict):
                continue
            rel = skill_file.relative_to(project_path)
            results.append(
                ConfigStatus(
                    name=str(rel),
                    config_type="skill_claude",
                    exists=True,
                    path=skill_file,
                )
            )

    cursor_rules_dir = project_path / ".cursor" / "rules"
    if safe_project_entry(cursor_rules_dir, project_path, strict=strict) and cursor_rules_dir.is_dir():
        for rule_file in _config_files(cursor_rules_dir, project_path, strict=strict):
            if rule_file.suffix == ".mdc" and _is_config_file(rule_file, strict=strict):
                results.append(ConfigStatus(str(rule_file.relative_to(project_path)), "cursorrules", True, rule_file))
    return results


def _is_config_file(path: Path, *, strict: bool) -> bool:
    """诊断模式保留元数据不可读的已知条目，稍后按单文件报错。"""
    try:
        if strict:
            metadata = path.lstat()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                return True
        return stat.S_ISREG(path.stat().st_mode)
    except FileNotFoundError:
        return False
    except OSError:
        return strict


def _config_files(directory: Path, root: Path, *, strict: bool = False):
    """受限遍历配置目录，不跟随链接、junction 或忽略目录。"""

    def on_error(error):
        if strict:
            raise error

    for current, directories, filenames in os.walk(directory, followlinks=False, onerror=on_error):
        current_path = Path(current)
        directories[:] = sorted(
            name
            for name in directories
            if name not in IGNORE_DIRS and safe_project_entry(current_path / name, root, strict=strict)
        )
        for name in sorted(filenames):
            path = current_path / name
            try:
                accepted = safe_project_entry(path, root, strict=strict)
            except OSError:
                # 无法读取元数据不是缺失；交给单文件诊断处理，仍不读正文。
                accepted = True
            # 严格诊断只记录链接本身，交给 CFG003；不读取目标正文。
            if accepted or strict:
                yield path


def has_any_agent_config(project_path: Path) -> bool:
    """检查项目是否已有任何 Agent 配置。"""
    return any(s.exists for s in scan_existing_configs(project_path))
