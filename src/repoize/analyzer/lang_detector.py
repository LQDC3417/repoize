"""语言检测器 — 通过文件扩展名统计识别项目主要语言"""

from collections import Counter
from pathlib import Path

from ..targets import safe_project_entry

# 文件扩展名到语言的映射
EXTENSION_MAP = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".swift": "Swift",
    ".php": "PHP",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".jl": "Julia",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".ml": "OCaml",
    ".clj": "Clojure",
    ".dart": "Dart",
    ".zig": "Zig",
    ".nim": "Nim",
    ".v": "V",
}

# 忽略的目录
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    ".output",
    "vendor",
    "third_party",
    "external",
    ".idea",
    ".vscode",
}


def detect_languages(project_path: Path, max_depth: int = 10, *, strict: bool = False) -> dict[str, float]:
    """扫描项目目录，返回语言及其文件占比。

    返回值: {"Python": 0.85, "JavaScript": 0.10, "TypeScript": 0.05}
    """
    counter: Counter[str] = Counter()
    project_path = Path(project_path)

    for file_path in _walk_files(project_path, max_depth, strict=strict):
        ext = file_path.suffix.lower()
        if ext in EXTENSION_MAP:
            counter[EXTENSION_MAP[ext]] += 1

    if not counter:
        return {}

    total = sum(counter.values())
    return {lang: count / total for lang, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))}


def get_primary_language(project_path: Path, *, strict: bool = False) -> str | None:
    """返回项目主语言名称，无文件则返回 None。"""
    langs = detect_languages(project_path, strict=strict)
    return next(iter(langs), None)


def _walk_files(root: Path, max_depth: int, *, strict: bool = False):
    """递归遍历文件，跳过忽略的目录，防御符号链接循环。"""
    visited: set[Path] = set()
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth or not safe_project_entry(current, root, strict=strict):
            continue
        try:
            real = current.resolve()
        except OSError:
            if strict:
                raise
            continue
        if real in visited:
            continue
        visited.add(real)
        try:
            for entry in current.iterdir():
                if not safe_project_entry(entry, root):
                    continue
                if entry.name.startswith(".") and entry.name not in {".github"}:
                    continue
                if entry.is_dir():
                    if entry.name not in IGNORE_DIRS:
                        stack.append((entry, depth + 1))
                elif entry.is_file():
                    yield entry
        except OSError:
            if strict:
                raise
            continue
