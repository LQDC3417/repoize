"""构建/测试/lint 命令提取器"""

import re
from pathlib import Path

from .dep_parser import _parse_pyproject
from .language_profiles import LanguageProfile
from .toml_utils import load_toml


class CommandSet:
    """项目命令集合。"""

    def __init__(self):
        """初始化命令集。"""
        self.build: list[str] = []
        self.test: list[str] = []
        self.lint: list[str] = []
        self.format: list[str] = []
        self.run: list[str] = []

    def to_dict(self) -> dict:
        """返回 JSON 可序列化的字典。"""
        return {
            "build": self.build,
            "test": self.test,
            "lint": self.lint,
            "format": self.format,
            "run": self.run,
        }


def extract_commands(
    project_path: Path,
    profile: LanguageProfile | None = None,
) -> CommandSet:
    """从项目配置文件中提取命令；profile 提供默认命令兜底。"""
    project_path = Path(project_path)
    cmds = CommandSet()

    _extract_from_pyproject(project_path, cmds)
    _extract_from_package_json(project_path, cmds)
    _extract_from_makefile(project_path, cmds)
    _extract_from_go(project_path, cmds)
    _extract_from_cargo(project_path, cmds)
    _extract_from_java(project_path, cmds)
    _extract_from_ruby(project_path, cmds)
    _extract_from_php(project_path, cmds)
    _apply_profile_defaults(cmds, profile)

    return cmds


def _extract_from_pyproject(project_path: Path, cmds: CommandSet):
    """从 pyproject.toml 提取命令。"""
    filepath = project_path / "pyproject.toml"
    config = load_toml(filepath)
    tool = config.get("tool", {})
    if not isinstance(tool, dict):
        tool = {}
    project = config.get("project", {})
    if not isinstance(project, dict):
        project = {}
    poetry = tool.get("poetry", {})
    if not isinstance(poetry, dict):
        poetry = {}

    # 检测测试框架
    poetry_deps = [poetry.get("dependencies", {}), poetry.get("dev-dependencies", {})]
    groups = poetry.get("group", {})
    if isinstance(groups, dict):
        poetry_deps.extend(group.get("dependencies", {}) for group in groups.values() if isinstance(group, dict))
    if (
        isinstance(tool.get("pytest"), dict)
        or any(dep.name.lower() == "pytest" for dep in _parse_pyproject(filepath))
        or any(isinstance(deps, dict) and "pytest" in deps for deps in poetry_deps)
    ):
        cmds.test.append("pytest")

    # 检测 lint 工具
    if isinstance(tool.get("ruff"), dict):
        cmds.lint.append("ruff check .")
        cmds.format.append("ruff format .")
    if isinstance(tool.get("mypy"), dict):
        cmds.lint.append("mypy .")
    if isinstance(tool.get("flake8"), dict):
        cmds.lint.append("flake8 .")
    if isinstance(tool.get("black"), dict):
        cmds.format.append("black .")
    if isinstance(tool.get("isort"), dict):
        cmds.format.append("isort .")

    # console script 的注册名就是可执行命令。
    for section in (project, poetry):
        scripts = section.get("scripts", {})
        if isinstance(scripts, dict):
            for name, entry in scripts.items():
                if section is poetry and isinstance(entry, dict):
                    entry = entry.get("reference")
                if isinstance(entry, str) and entry and name not in cmds.run:
                    cmds.run.append(name)


def _extract_from_package_json(project_path: Path, cmds: CommandSet):
    """从 package.json 提取 scripts。"""
    filepath = project_path / "package.json"
    if not filepath.exists():
        return

    try:
        import json

        data = json.loads(filepath.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, OSError, ValueError):
        return

    scripts = data.get("scripts", {})
    script_map = {
        "build": cmds.build,
        "test": cmds.test,
        "lint": cmds.lint,
        "format": cmds.format,
        "start": cmds.run,
        "dev": cmds.run,
    }
    for script_name, target_list in script_map.items():
        if script_name in scripts:
            target_list.append(f"npm run {script_name}")


def _extract_from_makefile(project_path: Path, cmds: CommandSet):
    """从 Makefile 提取常见目标。"""
    for makefile_name in ["Makefile", "makefile", "GNUmakefile"]:
        filepath = project_path / makefile_name
        if filepath.exists():
            break
    else:
        return

    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return

    # 提取顶层目标
    targets = re.findall(r"^([a-zA-Z][\w-]*)\s*:", content, re.MULTILINE)
    target_map = {
        "build": cmds.build,
        "test": cmds.test,
        "check": cmds.lint,
        "lint": cmds.lint,
        "fmt": cmds.format,
        "format": cmds.format,
        "run": cmds.run,
        "start": cmds.run,
        "serve": cmds.run,
        "dev": cmds.run,
    }
    for target in targets:
        target_lower = target.lower()
        if target_lower in target_map:
            cmd = f"make {target}"
            if cmd not in target_map[target_lower]:
                target_map[target_lower].append(cmd)


def _extract_from_go(project_path: Path, cmds: CommandSet):
    """Go 项目命令提取。"""
    if (project_path / "go.mod").exists():
        cmds.build.append("go build ./...")
        cmds.test.append("go test ./...")
        cmds.lint.append("golangci-lint run")


def _extract_from_cargo(project_path: Path, cmds: CommandSet):
    """Rust 项目命令提取。"""
    if (project_path / "Cargo.toml").exists():
        cmds.build.append("cargo build")
        cmds.test.append("cargo test")
        cmds.lint.append("cargo clippy")
        cmds.format.append("cargo fmt")
        cmds.run.append("cargo run")


def _apply_profile_defaults(cmds: CommandSet, profile: LanguageProfile | None):
    """只在对应分类为空时填充 profile 默认命令。"""
    if profile is None:
        return
    target_map = {
        "build": cmds.build,
        "test": cmds.test,
        "lint": cmds.lint,
        "format": cmds.format,
        "run": cmds.run,
    }
    for category, commands in profile.commands.items():
        target = target_map.get(category)
        if target is not None and not target:
            target.extend(commands)


def _extract_from_java(project_path: Path, cmds: CommandSet):
    """Java Maven/Gradle 命令提取。"""
    if (project_path / "pom.xml").exists():
        cmds.build.append("mvn verify")
        cmds.test.append("mvn test")
        cmds.lint.append("mvn checkstyle:check")
    elif (project_path / "build.gradle").exists():
        cmds.build.append("gradle build")
        cmds.test.append("gradle test")
        cmds.lint.append("gradle check")


def _extract_from_ruby(project_path: Path, cmds: CommandSet):
    """Ruby Rake/RuboCop 命令提取。"""
    if (project_path / "Gemfile").exists():
        cmds.build.append("bundle exec rake build")
        cmds.test.append("bundle exec rake test")
        cmds.lint.append("bundle exec rubocop")


def _extract_from_php(project_path: Path, cmds: CommandSet):
    """PHP composer scripts 提取，无 scripts 时给出 phpunit 默认。"""
    filepath = project_path / "composer.json"
    if not filepath.exists():
        return
    try:
        import json

        data = json.loads(filepath.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, OSError, ValueError):
        return

    scripts = data.get("scripts", {})
    script_map = {
        "build": cmds.build,
        "test": cmds.test,
        "lint": cmds.lint,
        "format": cmds.format,
    }
    for script_name, target_list in script_map.items():
        if script_name in scripts:
            target_list.append(f"composer run {script_name}")
    if not cmds.test:
        cmds.test.append("vendor/bin/phpunit")
