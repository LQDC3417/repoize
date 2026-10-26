"""已有 Agent 配置文件扫描器"""

from pathlib import Path

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


def scan_existing_configs(project_path: Path) -> list[ConfigStatus]:
    """扫描项目中已有的 Agent 配置文件。"""
    project_path = Path(project_path)
    results: list[ConfigStatus] = []

    for filename, config_type in AGENT_CONFIGS.items():
        filepath = project_path / filename
        results.append(
            ConfigStatus(
                name=filename,
                config_type=config_type,
                exists=filepath.is_file(),
                path=filepath,
            )
        )

    # 检查 .claude/ 目录下的 skills
    claude_skills_dir = project_path / ".claude" / "skills"
    if claude_skills_dir.is_dir():
        for skill_file in claude_skills_dir.rglob("SKILL.md"):
            if not skill_file.is_file():
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
    if cursor_rules_dir.is_dir():
        for rule_file in sorted(cursor_rules_dir.rglob("*.mdc")):
            if rule_file.is_file():
                results.append(ConfigStatus(str(rule_file.relative_to(project_path)), "cursorrules", True, rule_file))
    return results


def has_any_agent_config(project_path: Path) -> bool:
    """检查项目是否已有任何 Agent 配置。"""
    return any(s.exists for s in scan_existing_configs(project_path))
