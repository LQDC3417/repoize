"""生成目标与旧配置的安全决策。"""

import stat
from pathlib import Path

MCP_TARGET = ".mcp.json"
CURSOR_TARGET = ".cursor/rules/repoize.mdc"


def safe_project_entry(path: Path, project_path: Path, *, strict: bool = False) -> bool:
    """读取和遍历前拒绝项目外路径及所有层级的链接或 reparse point。"""
    root = Path(project_path).absolute()
    path = Path(path).absolute()
    try:
        relative = path.relative_to(root)
        for current in (root, *(root.joinpath(*relative.parts[:i]) for i in range(1, len(relative.parts) + 1))):
            metadata = current.lstat()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                return False
        return path.resolve().is_relative_to(root.resolve())
    except (FileNotFoundError, ValueError):
        return False
    except OSError:
        if strict:
            raise
        return False


def safe_output_path(project_path: Path, filename: str) -> Path:
    """拒绝目录、链接、junction 和越出项目根目录的目标。"""
    root = Path(project_path).absolute()
    relative = Path(filename)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("输出路径不能越出项目根目录")
    output = root / relative
    if not root.is_dir():
        raise ValueError("项目路径必须是目录")
    for current in (root, *(root.joinpath(*relative.parts[:i]) for i in range(1, len(relative.parts) + 1))):
        if current.is_symlink():
            raise ValueError(f"拒绝写入符号链接: {current}")
        if current.exists() and getattr(current.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"拒绝写入 reparse point/junction: {current}")
    if not output.resolve().is_relative_to(root.resolve()):
        raise ValueError("输出路径不能越出项目根目录")
    if output.exists() and not output.is_file():
        raise IsADirectoryError(f"输出目标不是普通文件: {output}")
    return output


def legacy_decision(project_path: Path, filename: str) -> str | None:
    """旧路径只提示手动迁移；MCP 并存时保留旧文件。"""
    legacy_name = {MCP_TARGET: ".claude/mcp.json", CURSOR_TARGET: ".cursorrules"}.get(filename)
    if not legacy_name:
        return None
    legacy = project_path / legacy_name
    if not legacy.exists() and not legacy.is_symlink():
        return None
    modern_exists = (project_path / filename).is_file()
    if filename == CURSOR_TARGET or not modern_exists:
        raise ValueError(f"检测到旧配置 {legacy_name}，请手动迁移到 {filename}")
    return f"{legacy_name} 与 {filename} 并存：仅处理新文件，请手动迁移旧配置；不会自动合并"
