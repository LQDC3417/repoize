"""代码质量分析器：分析项目的代码质量指标。"""

from __future__ import annotations

import os
import re
from configparser import ConfigParser
from configparser import Error as ConfigError
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from ..targets import safe_project_entry
from .lang_detector import IGNORE_DIRS
from .toml_utils import load_toml

if TYPE_CHECKING:
    from .language_profiles import LanguageProfile

# 代码文件扩展名
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".swift",
    ".kt",
    ".scala",
    ".clj",
    ".ex",
    ".exs",
    ".erl",
    ".hs",
}


@dataclass
class CodeQualityMetrics:
    """代码质量指标。"""

    total_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0

    # 文件统计
    files_by_language: dict[str, int] = field(default_factory=dict)
    lines_by_language: dict[str, int] = field(default_factory=dict)

    # 代码复杂度指标
    avg_function_length: float = 0.0
    max_function_length: int = 0

    # 代码重复指标
    duplicate_files: int = 0
    duplicate_lines: int = 0

    # 代码质量工具
    quality_tools_found: list[str] = field(default_factory=list)
    quality_config_found: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """返回 JSON 可序列化的字典。"""
        return {
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "files_by_language": self.files_by_language,
            "lines_by_language": self.lines_by_language,
            "avg_function_length": self.avg_function_length,
            "max_function_length": self.max_function_length,
            "duplicate_files": self.duplicate_files,
            "duplicate_lines": self.duplicate_lines,
            "quality_tools_found": self.quality_tools_found,
            "quality_config_found": self.quality_config_found,
        }


def analyze_code_quality(
    project_path: Path,
    profile: LanguageProfile | None = None,
    dependencies: list[str] | None = None,
) -> CodeQualityMetrics:
    """分析项目的代码质量。

    Args:
        project_path: 项目根目录
        profile: 语言画像
        dependencies: 依赖列表

    Returns:
        CodeQualityMetrics: 代码质量指标
    """
    metrics = CodeQualityMetrics()

    # 统计文件和行数
    _count_files_and_lines(project_path, metrics)

    # 检测代码质量工具
    _detect_quality_tools(project_path, profile, dependencies, metrics)

    # 检测代码质量配置文件
    _detect_quality_configs(project_path, metrics)

    # 计算代码复杂度（简化版）
    _calculate_complexity(project_path, metrics)

    # 检测代码重复（简化版）
    _detect_duplicates(project_path, metrics)

    return metrics


def _walk_code_files(project_path: Path):
    """质量分析统一跳过依赖目录、链接和非普通文件。"""
    if not safe_project_entry(project_path, project_path):
        return
    for current, directories, filenames in os.walk(project_path, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            name
            for name in directories
            if name not in IGNORE_DIRS
            and (not name.startswith(".") or name == ".github")
            and safe_project_entry(current_path / name, project_path)
        )
        for name in sorted(filenames):
            path = current_path / name
            if (
                not name.startswith(".")
                and path.suffix in CODE_EXTENSIONS
                and safe_project_entry(path, project_path)
                and path.is_file()
            ):
                yield path


def _count_files_and_lines(project_path: Path, metrics: CodeQualityMetrics) -> None:
    """统计文件数量和行数。"""
    for file_path in _walk_code_files(project_path):
        metrics.total_files += 1
        lang = _get_language_from_extension(file_path.suffix)
        metrics.files_by_language[lang] = metrics.files_by_language.get(lang, 0) + 1
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                total = len(lines)
                metrics.total_lines += total
                metrics.lines_by_language[lang] = metrics.lines_by_language.get(lang, 0) + total
                for line in lines:
                    line = line.strip()
                    if not line:
                        metrics.blank_lines += 1
                    elif line.startswith(("#", "//", "/*", "*", "<!--")):
                        metrics.comment_lines += 1
                    else:
                        metrics.code_lines += 1
        except (OSError, UnicodeDecodeError):
            pass


def _get_language_from_extension(ext: str) -> str:
    """根据文件扩展名返回语言名称。"""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript (JSX)",
        ".tsx": "TypeScript (TSX)",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".php": "PHP",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".clj": "Clojure",
        ".ex": "Elixir",
        ".exs": "Elixir Script",
        ".erl": "Erlang",
        ".hs": "Haskell",
    }
    return ext_map.get(ext, "Unknown")


def _detect_quality_tools(
    project_path: Path,
    profile: LanguageProfile | None,
    dependencies: list[str] | None,
    metrics: CodeQualityMetrics,
) -> None:
    """检测代码质量工具。"""
    tools_found: set[str] = set()

    # 从不同来源检测质量工具
    tools_found.update(_detect_tools_from_dependencies(profile, dependencies))
    tools_found.update(_detect_tools_from_pyproject(project_path))
    tools_found.update(_detect_tools_from_config_files(project_path))

    metrics.quality_tools_found = sorted(tools_found)


def _detect_tools_from_dependencies(
    profile: LanguageProfile | None,
    dependencies: list[str] | None,
) -> set[str]:
    """从项目依赖中检测质量工具。"""
    tools: set[str] = set()
    if profile and dependencies:
        for tool in profile.quality_tools:
            if any(tool in dep.lower() for dep in dependencies):
                tools.add(tool)
    return tools


def _detect_tools_from_pyproject(project_path: Path) -> set[str]:
    """从 pyproject.toml 配置节检测质量工具。"""
    path = project_path / "pyproject.toml"
    if not safe_project_entry(path, project_path) or not path.is_file():
        return set()
    tool_section = load_toml(path).get("tool", {})
    if not isinstance(tool_section, dict):
        return set()
    return {
        tool_name
        for tool_name in ["ruff", "mypy", "pytest", "black", "isort", "pylint", "flake8"]
        if isinstance(tool_section.get(tool_name), dict)
    }


def _setup_cfg_sections(project_path: Path) -> set[str]:
    """共享 INI 配置只采信真实配置节，禁用不必要的插值。"""
    path = project_path / "setup.cfg"
    if not safe_project_entry(path, project_path) or not path.is_file():
        return set()
    parser = ConfigParser(interpolation=None)
    try:
        parser.read_string(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ConfigError):
        return set()
    return set(parser.sections())


def _detect_tools_from_config_files(project_path: Path) -> set[str]:
    """从独立配置文件检测质量工具。"""
    tools: set[str] = set()
    config_tool_map = {
        ".eslintrc": "eslint",
        ".eslintrc.js": "eslint",
        ".eslintrc.json": "eslint",
        ".eslintrc.yml": "eslint",
        ".prettierrc": "prettier",
        ".prettierrc.js": "prettier",
        ".prettierrc.json": "prettier",
        ".prettierrc.yml": "prettier",
        ".flake8": "flake8",
        "tox.ini": "tox",
        ".pylintrc": "pylint",
        "mypy.ini": "mypy",
        ".mypy.ini": "mypy",
    }

    for config_file, tool_name in config_tool_map.items():
        path = project_path / config_file
        if safe_project_entry(path, project_path) and path.is_file():
            tools.add(tool_name)
    if "flake8" in _setup_cfg_sections(project_path):
        tools.add("flake8")
    return tools


def _detect_quality_configs(project_path: Path, metrics: CodeQualityMetrics) -> None:
    """检测代码质量配置文件。"""
    quality_configs = [
        # Python
        ".flake8",
        "setup.cfg",
        "pyproject.toml",
        "tox.ini",
        ".pylintrc",
        ".mypy.ini",
        "mypy.ini",
        # JavaScript/TypeScript
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".prettierrc",
        ".prettierrc.js",
        ".prettierrc.json",
        ".prettierrc.yml",
        "tsconfig.json",
        # Go
        ".golangci.yml",
        ".golangci.yaml",
        # Rust
        "rustfmt.toml",
        ".rustfmt.toml",
        "clippy.toml",
        # Java
        "checkstyle.xml",
        "spotbugs.xml",
        "pmd.xml",
        # Ruby
        ".rubocop.yml",
        # PHP
        ".php-cs-fixer.php",
        ".php_cs",
        "phpstan.neon",
        # 通用
        ".editorconfig",
        ".gitattributes",
    ]

    for config in quality_configs:
        if config == "setup.cfg" and not any(
            section in {"flake8", "tool:pytest", "mypy", "isort"}
            or section.startswith(("coverage:", "mypy-", "pylint."))
            for section in _setup_cfg_sections(project_path)
        ):
            continue
        path = project_path / config
        if safe_project_entry(path, project_path) and path.is_file():
            metrics.quality_config_found.append(config)


def _calculate_complexity(project_path: Path, metrics: CodeQualityMetrics) -> None:
    """计算代码复杂度（简化版）。"""
    function_lengths: list[int] = []

    for file_path in _walk_code_files(project_path):
        lengths = _extract_function_lengths(file_path)
        function_lengths.extend(lengths)

    if function_lengths:
        metrics.avg_function_length = sum(function_lengths) / len(function_lengths)
        metrics.max_function_length = max(function_lengths)


def _extract_function_lengths(file_path: Path) -> list[int]:
    """提取文件中的函数长度列表。"""
    lengths: list[int] = []
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

            if file_path.suffix == ".py":
                lengths = _extract_python_function_lengths(content)
            elif file_path.suffix in (".js", ".ts", ".jsx", ".tsx"):
                lengths = _extract_js_ts_function_lengths(content)

    except (OSError, UnicodeDecodeError):
        pass
    return lengths


def _extract_python_function_lengths(content: str) -> list[int]:
    """提取Python函数的长度。"""
    lengths: list[int] = []
    functions = re.findall(r"def\s+\w+\s*\(.*?\):", content)
    for func in functions:
        func_start = content.find(func)
        if func_start != -1:
            next_func = content.find("\ndef ", func_start + 1)
            func_body = content[func_start:] if next_func == -1 else content[func_start:next_func]
            lengths.append(func_body.count("\n") + 1)
    return lengths


def _extract_js_ts_function_lengths(content: str) -> list[int]:
    """提取JavaScript/TypeScript函数的长度。"""
    lengths: list[int] = []
    functions = re.findall(r"(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:function|\(.*?\)\s*=>))", content)
    for func in functions:
        func_start = content.find(func)
        if func_start != -1:
            lengths.append(content[func_start:].count("\n") + 1)
    return lengths


def _detect_duplicates(project_path: Path, metrics: CodeQualityMetrics) -> None:
    """检测代码重复（简化版）。"""
    # 这里只做简单的文件内容比较
    # 实际的重复检测需要更复杂的算法

    file_hashes: dict[str, list[Path]] = {}

    for file_path in _walk_code_files(project_path):
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # 简单的哈希比较
                content_hash = hash(content)
                if content_hash in file_hashes:
                    file_hashes[content_hash].append(file_path)
                else:
                    file_hashes[content_hash] = [file_path]
        except (OSError, UnicodeDecodeError):
            pass

    # 统计重复文件
    for _hash_val, files in file_hashes.items():
        if len(files) > 1:
            metrics.duplicate_files += len(files) - 1
            # 简单统计重复行数（取第一个文件的行数）
            try:
                with open(files[0], encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    metrics.duplicate_lines += len(lines) * (len(files) - 1)
            except (OSError, UnicodeDecodeError):
                pass
