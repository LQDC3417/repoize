"""文本配置格式校验，供生成和检查共用。"""

import re
from pathlib import Path

import yaml

GENERATED_START = "<!-- repoize:generated-start -->"
GENERATED_END = "<!-- repoize:generated-end -->"


def marker_bounds(content: str) -> tuple[int, int] | None:
    """只接受一对完整且顺序正确的生成标记。"""
    starts, ends = content.count(GENERATED_START), content.count(GENERATED_END)
    if not starts and not ends:
        return None
    if starts != 1 or ends != 1 or content.index(GENERATED_START) >= content.index(GENERATED_END):
        raise ValueError("managed marker 不完整、重复或顺序错误")
    return content.index(GENERATED_START), content.index(GENERATED_END) + len(GENERATED_END)


def split_frontmatter(content: str, filename: str) -> tuple[str, str]:
    """安全解析元数据并保留原始头部字节对应的文本。"""
    target = Path(filename)
    is_skill = target.name == "SKILL.md"
    if not is_skill and target.suffix != ".mdc":
        return "", content
    match = re.match(r"\A\ufeff?---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.DOTALL)
    if match is None:
        raise ValueError("缺少合法的首行 frontmatter；旧格式需要手动迁移")
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        location = f"（行 {mark.line + 2}，列 {mark.column + 1}）" if mark else ""
        raise ValueError(f"无效 YAML frontmatter{location}") from None
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter 必须是对象")
    if is_skill:
        name = metadata.get("name")
        if (
            not isinstance(name, str)
            or not 1 <= len(name) <= 64
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
            or name != target.parent.name
        ):
            raise ValueError("Skill name 必须是与目录名匹配的字符串")
        description = metadata.get("description")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            raise ValueError("Skill description 必须是 1–1024 字符的非空字符串")
    else:
        for key, expected in (("description", str), ("alwaysApply", bool)):
            if key in metadata and not isinstance(metadata[key], expected):
                raise ValueError(f"Cursor {key} 类型错误")
        globs = metadata.get("globs", "")
        if not isinstance(globs, str) and not (
            isinstance(globs, list) and all(isinstance(item, str) for item in globs)
        ):
            raise ValueError("Cursor globs 类型错误")
    return content[: match.end()], content[match.end() :]
