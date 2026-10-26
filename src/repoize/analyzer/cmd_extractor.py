"""只读提取命令及来源；候选命令从不在分析过程中执行。"""

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..targets import safe_project_entry
from .language_profiles import LanguageProfile
from .toml_utils import tomllib

CATEGORIES = ("build", "test", "lint", "format", "run")


@dataclass(frozen=True)
class CommandSource:
    """命令的声明位置或推断依据。"""

    kind: str
    path: str | None = None
    selector: str | None = None


@dataclass
class CommandEvidence:
    """一个分类内去重的命令及其全部来源。"""

    category: str
    command: str
    sources: list[CommandSource] = field(default_factory=list)
    verification: str = "not_run"


class CommandSet:
    """兼容旧五组字符串接口，同时保留生成及诊断证据。"""

    def __init__(self):
        """初始化命令集。"""
        self.setup: list[str] = []
        self.build: list[str] = []
        self.test: list[str] = []
        self.lint: list[str] = []
        self.format: list[str] = []
        self.run: list[str] = []
        self.evidence: list[CommandEvidence] = []
        self.issues: list[dict] = []

    def add(self, category: str, command: str, source: CommandSource) -> None:
        """同分类去重，并合并多处来源。"""
        commands = getattr(self, category)
        if command not in commands:
            commands.append(command)
        item = next((item for item in self.evidence if (item.category, item.command) == (category, command)), None)
        if item is None:
            item = CommandEvidence(category, command)
            self.evidence.append(item)
        if source not in item.sources:
            item.sources.append(source)

    def to_dict(self) -> dict:
        """保持 analysis v1 的五组字符串结构。"""
        return {category: getattr(self, category) for category in CATEGORIES}

    def generation_dict(self) -> dict:
        """生成只使用具有声明或项目推断依据的命令。"""
        supported = {
            (item.category, item.command)
            for item in self.evidence
            if any(source.kind in {"declared", "inferred"} for source in item.sources)
        }
        return {
            category: [command for command in getattr(self, category) if (category, command) in supported]
            for category in ("setup", *CATEGORIES)
        }

    def evidence_dict(self) -> list[dict]:
        """返回排序稳定且可独立序列化的证据。"""
        results = []
        for item in sorted(self.evidence, key=lambda item: (item.category, item.command)):
            result = asdict(item)
            result["sources"] = [
                asdict(source)
                for source in sorted(
                    item.sources, key=lambda source: (source.kind, source.path or "", source.selector or "")
                )
            ]
            results.append(result)
        return results

    def issue(self, path: str, reason: str, rule_id: str = "SRC001") -> None:
        """诊断只报告原因类别，避免泄漏源文件原文。"""
        finding = {
            "rule_id": rule_id,
            "severity": "warning" if rule_id == "CMD002" else "error",
            "type": None,
            "path": path,
            "message": reason,
            "evidence": [],
            "suggestion": "Review the declaration file and resolve the reported issue.",
        }
        if finding not in self.issues:
            self.issues.append(finding)


def _read(project_path: Path, filename: str, cmds: CommandSet) -> str | None:
    """只读取项目内普通文件，缺失与不可读分别处理。"""
    path = project_path / filename
    try:
        path.lstat()
    except FileNotFoundError:
        return None
    except OSError:
        cmds.issue(filename, "Declaration metadata is unreadable.")
        return None
    if not safe_project_entry(path, project_path):
        cmds.issue(filename, "Declaration is not a safe project file (link or reparse point).")
        return None
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        cmds.issue(filename, "Declaration is unreadable or is not UTF-8.")
        return None


def _manifest(project_path: Path, filename: str, cmds: CommandSet) -> dict | None:
    """解析已有 JSON/TOML 声明，并保留安全的失败类别。"""
    text = _read(project_path, filename, cmds)
    if text is None:
        return None
    try:
        data = json.loads(text) if filename.endswith(".json") else tomllib.loads(text)
    except (ValueError, RecursionError):
        cmds.issue(filename, "Declaration has invalid JSON/TOML syntax.")
        return None
    if not isinstance(data, dict):
        cmds.issue(filename, "Declaration root must be an object.")
        return None
    return data


def _table(data: dict, key: str, filename: str, cmds: CommandSet) -> dict:
    """提取对象字段，错误结构可诊断且不抛出异常。"""
    value = data.get(key, {})
    if not isinstance(value, dict):
        cmds.issue(filename, "Declaration contains an invalid object field.")
        return {}
    return value


def extract_commands(project_path: Path, profile: LanguageProfile | None = None) -> CommandSet:
    """复用项目声明推断命令，语言画像只作为未验证建议。"""
    project_path = Path(project_path).absolute()
    cmds = CommandSet()
    _extract_from_pyproject(project_path, cmds)
    runner = _extract_from_package_json(project_path, cmds)
    _extract_from_makefile(project_path, cmds)
    _extract_from_go(project_path, cmds)
    _extract_from_cargo(project_path, cmds)
    java_runner = _extract_from_java(project_path, cmds)
    _extract_from_ruby(project_path, cmds)
    _extract_from_php(project_path, cmds)
    if profile is not None:
        for category, commands in {"setup": profile.setup_commands, **profile.commands}.items():
            if category not in ("setup", *CATEGORIES) or getattr(cmds, category):
                continue
            if (profile.name == "Python" and category == "setup") or (profile.name == "Java" and not java_runner):
                continue
            if profile.name in {"JavaScript", "TypeScript"} and runner is False:
                continue
            for command in commands:
                if profile.name == "Java" and java_runner and not command.startswith(java_runner):
                    continue
                if profile.name in {"JavaScript", "TypeScript"} and isinstance(runner, str):
                    command = re.sub(r"^npm\b", runner, command)
                cmds.add(category, command, CommandSource("suggested", selector=f"profile:{profile.name}"))
    return cmds


def _extract_from_pyproject(root: Path, cmds: CommandSet) -> None:
    """记录 Python 工具、依赖、console script 及安装依据。"""
    filename = "pyproject.toml"
    config = _manifest(root, filename, cmds)
    if config is not None:
        project = _table(config, "project", filename, cmds)
        tool = _table(config, "tool", filename, cmds)
        poetry = _table(tool, "poetry", filename, cmds)
        optional = _table(project, "optional-dependencies", filename, cmds)
        dependencies = [("project.dependencies", project.get("dependencies", []))]
        dependencies.extend((f"project.optional-dependencies.{name}", value) for name, value in optional.items())
        dependencies.extend(
            (f"tool.poetry.{key}", _table(poetry, key, filename, cmds)) for key in ("dependencies", "dev-dependencies")
        )
        groups = _table(poetry, "group", filename, cmds)
        for name, group in groups.items():
            if isinstance(group, dict):
                dependencies.append(
                    (f"tool.poetry.group.{name}.dependencies", _table(group, "dependencies", filename, cmds))
                )
            else:
                cmds.issue(filename, "Declaration contains an invalid dependency group.")
        tool_commands = {
            "pytest": (("test", "pytest"),),
            "ruff": (("lint", "ruff check ."), ("format", "ruff format .")),
            "mypy": (("lint", "mypy ."),),
            "flake8": (("lint", "flake8 ."),),
            "black": (("format", "black ."),),
            "isort": (("format", "isort ."),),
        }
        for name, commands in tool_commands.items():
            sources = []
            if isinstance(tool.get(name), dict):
                sources.append(CommandSource("inferred", filename, f"tool.{name}"))
            elif name in tool:
                cmds.issue(filename, "Declaration contains an invalid tool configuration field.")
            for selector, values in dependencies:
                expected_type = list if selector.startswith("project.") else dict
                if not isinstance(values, expected_type):
                    cmds.issue(filename, "Declaration contains an invalid dependency collection.")
                    continue
                if isinstance(values, list) and any(not isinstance(value, str) for value in values):
                    cmds.issue(filename, "Declaration contains an invalid dependency value.")
                if isinstance(values, dict) and any(not isinstance(value, (str, dict)) for value in values.values()):
                    cmds.issue(filename, "Declaration contains an invalid dependency value.")
                    values = {name: value for name, value in values.items() if isinstance(value, (str, dict))}
                names = [
                    re.split(r"[\s\[<>=!~;@]", value.strip(), maxsplit=1)[0].lower().replace("_", "-")
                    for value in values
                    if isinstance(value, str)
                ]
                if name in names:
                    sources.append(CommandSource("inferred", filename, selector))
            for category, command in commands:
                for source in sources:
                    cmds.add(category, command, source)
        for selector, section in (("project", project), ("tool.poetry", poetry)):
            for name, entry in _table(section, "scripts", filename, cmds).items():
                if selector == "tool.poetry" and isinstance(entry, dict):
                    entry = entry.get("reference")
                if isinstance(entry, str) and entry.strip() and name.strip():
                    cmds.add("run", name, CommandSource("declared", filename, f"{selector}.scripts.{name}"))
                else:
                    cmds.issue(filename, "Declaration contains an invalid script value.")
        if isinstance(optional.get("dev"), list) and all(isinstance(value, str) for value in optional["dev"]):
            cmds.add(
                "setup",
                'pip install -e ".[dev]"',
                CommandSource("inferred", filename, "project.optional-dependencies.dev"),
            )
        elif project.get("name") or poetry.get("name"):
            cmds.add(
                "setup",
                "pip install -e .",
                CommandSource("inferred", filename, "project" if project else "tool.poetry"),
            )
    if not cmds.setup:
        for filename in ("setup.py", "setup.cfg"):
            if _read(root, filename, cmds) is not None:
                cmds.add("setup", "pip install -e .", CommandSource("inferred", filename))
    for filename in ("requirements.txt", "requirements-dev.txt"):
        if _read(root, filename, cmds) is not None:
            cmds.add("setup", f"pip install -r {filename}", CommandSource("inferred", filename))


def _extract_from_package_json(root: Path, cmds: CommandSet) -> str | bool | None:
    """优先声明的包管理器，再使用一致的锁文件，否则 npm 标准入口。"""
    filename = "package.json"
    data = _manifest(root, filename, cmds)
    if data is None:
        return None
    declared = data.get("packageManager")
    runner = declared.split("@", 1)[0] if isinstance(declared, str) else None
    locks = {
        "package-lock.json": "npm",
        "npm-shrinkwrap.json": "npm",
        "pnpm-lock.yaml": "pnpm",
        "yarn.lock": "yarn",
        "bun.lock": "bun",
        "bun.lockb": "bun",
    }
    found = [
        (name, manager)
        for name, manager in locks.items()
        if safe_project_entry(root / name, root) and (root / name).is_file()
    ]
    managers = {manager for _, manager in found}
    if declared is not None and runner not in {"npm", "pnpm", "yarn", "bun"}:
        cmds.issue(filename, "Package manager declaration is unsupported or invalid.", "CMD002")
        return False
    if len(managers) > 1 or (runner and managers and managers != {runner}):
        cmds.issue(filename, "Package manager declaration and lock files conflict.", "CMD002")
        return False
    sources = [CommandSource("inferred", name, "lockfile") for name, _ in found]
    if runner:
        sources.append(CommandSource("declared", filename, "packageManager"))
    elif managers:
        runner = next(iter(managers))
    else:
        runner = "npm"
        sources.append(CommandSource("inferred", filename, "scripts (npm default runner)"))
    cmds.add("setup", f"{runner} install", CommandSource("inferred", filename))
    for source in sources:
        cmds.add("setup", f"{runner} install", source)
    scripts = _table(data, "scripts", filename, cmds)
    for name, category in {
        "build": "build",
        "test": "test",
        "lint": "lint",
        "format": "format",
        "start": "run",
        "dev": "run",
    }.items():
        if name in scripts and isinstance(scripts[name], str) and scripts[name].strip():
            command = f"{runner} run {name}"
            cmds.add(category, command, CommandSource("declared", filename, f"scripts.{name}"))
            for source in sources:
                cmds.add(category, command, source)
        elif name in scripts:
            cmds.issue(filename, "Declaration contains an invalid script value.")
    return runner


def _extract_from_makefile(root: Path, cmds: CommandSet) -> None:
    """只分析原有的常见顶层目标。"""
    categories = {
        "build": "build",
        "test": "test",
        "check": "lint",
        "lint": "lint",
        "fmt": "format",
        "format": "format",
        "run": "run",
        "start": "run",
        "serve": "run",
        "dev": "run",
    }
    for filename in ("Makefile", "makefile", "GNUmakefile"):
        content = _read(root, filename, cmds)
        if content is None:
            continue
        for target in re.findall(r"^([a-zA-Z][\w-]*)\s*:", content, re.MULTILINE):
            if target.lower() in categories:
                cmds.add(categories[target.lower()], f"make {target}", CommandSource("declared", filename, target))
        break


def _extract_from_go(root: Path, cmds: CommandSet) -> None:
    """Go 标准命令可由模块推断，可选工具必须单独声明。"""
    content = _read(root, "go.mod", cmds)
    if content is None:
        return
    for category, command in (
        ("setup", "go mod download"),
        ("build", "go build ./..."),
        ("test", "go test ./..."),
        ("format", "gofmt -w ."),
    ):
        cmds.add(category, command, CommandSource("inferred", "go.mod"))
    declared = False
    in_require = False
    for line in content.splitlines():
        line = line.split("//", 1)[0].strip()
        if line.startswith("require ("):
            in_require = True
        elif line == ")":
            in_require = False
        elif in_require or line.startswith("require "):
            parts = line.removeprefix("require ").split()
            if len(parts) >= 2 and re.fullmatch(r"github\.com/golangci/golangci-lint(?:/v\d+)?", parts[0]):
                declared = True
    source = CommandSource("inferred", "go.mod", "require:golangci-lint") if declared else CommandSource("suggested")
    cmds.add("lint", "golangci-lint run", source)


def _extract_from_cargo(root: Path, cmds: CommandSet) -> None:
    """Rust 标准命令来源于可解析 Cargo 声明。"""
    if _manifest(root, "Cargo.toml", cmds) is None:
        return
    for category, command in (
        ("setup", "cargo build"),
        ("build", "cargo build"),
        ("test", "cargo test"),
        ("lint", "cargo clippy"),
        ("format", "cargo fmt"),
        ("run", "cargo run"),
    ):
        cmds.add(category, command, CommandSource("inferred", "Cargo.toml"))


def _extract_from_java(root: Path, cmds: CommandSet) -> str | None:
    """依实际 Maven 或 Gradle 文件选用一套命令。"""
    content = _read(root, "pom.xml", cmds)
    if content is not None:
        try:
            element = ET.fromstring(content)
        except (ET.ParseError, ValueError):
            cmds.issue("pom.xml", "Declaration has invalid XML syntax.")
            return "mvn"
        artifacts = {node.text for node in element.iter() if node.tag.rsplit("}", 1)[-1] == "artifactId"}
        for category, command in (
            ("setup", "mvn -q dependency:resolve"),
            ("build", "mvn verify"),
            ("test", "mvn test"),
        ):
            cmds.add(category, command, CommandSource("inferred", "pom.xml"))
        kind = "inferred" if "maven-checkstyle-plugin" in artifacts else "suggested"
        cmds.add("lint", "mvn checkstyle:check", CommandSource(kind, "pom.xml", "maven-checkstyle-plugin"))
        kind = "inferred" if "spotless-maven-plugin" in artifacts else "suggested"
        cmds.add("format", "mvn spotless:apply", CommandSource(kind, "pom.xml", "spotless-maven-plugin"))
        return "mvn"
    for filename in ("build.gradle", "build.gradle.kts"):
        content = _read(root, filename, cmds)
        if content is None:
            continue
        for category, command in (
            ("setup", "gradle dependencies"),
            ("build", "gradle build"),
            ("test", "gradle test"),
            ("lint", "gradle check"),
        ):
            cmds.add(category, command, CommandSource("inferred", filename))
        # 注释和普通字符串整体跳过，只识别直接的 id 插件声明。
        declarations = re.finditer(
            r"""//[^\r\n]*|/\*.*?\*/"""
            r"""|(?P<plugin>\bid\s*\(?\s*['"](?:com\.diffplug\.)?spotless['"])"""
            r"""|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'""",
            content,
            re.DOTALL,
        )
        kind = "inferred" if any(match.group("plugin") for match in declarations) else "suggested"
        cmds.add("format", "gradle spotlessApply", CommandSource(kind, filename, "spotless"))
        return "gradle"
    return None


def _extract_from_ruby(root: Path, cmds: CommandSet) -> None:
    """Gemfile 只能证明依赖存在，不证明 Rake 目标存在。"""
    content = _read(root, "Gemfile", cmds)
    if content is None:
        return
    cmds.add("setup", "bundle install", CommandSource("inferred", "Gemfile"))
    for category, command in (("build", "bundle exec rake build"), ("test", "bundle exec rake test")):
        cmds.add(category, command, CommandSource("suggested", "Gemfile"))
    kind = "inferred" if re.search(r"^\s*gem\s+['\"]rubocop['\"]", content, re.MULTILINE) else "suggested"
    cmds.add("lint", "bundle exec rubocop", CommandSource(kind, "Gemfile", "gem rubocop"))


def _extract_from_php(root: Path, cmds: CommandSet) -> None:
    """Composer scripts 保留声明；phpunit 依赖才支持默认测试入口。"""
    filename = "composer.json"
    data = _manifest(root, filename, cmds)
    if data is None:
        return
    cmds.add("setup", "composer install", CommandSource("inferred", filename))
    for name, value in _table(data, "scripts", filename, cmds).items():
        if name not in CATEGORIES:
            continue
        if isinstance(value, str) or (isinstance(value, list) and all(isinstance(item, str) for item in value)):
            cmds.add(name, f"composer run {name}", CommandSource("declared", filename, f"scripts.{name}"))
        else:
            cmds.issue(filename, "Declaration contains an invalid script value.")
    if not cmds.test:
        for key in ("require", "require-dev"):
            if "phpunit/phpunit" in _table(data, key, filename, cmds):
                cmds.add("test", "vendor/bin/phpunit", CommandSource("inferred", filename, f"{key}.phpunit/phpunit"))
        if not cmds.test:
            cmds.add("test", "vendor/bin/phpunit", CommandSource("suggested", filename))
