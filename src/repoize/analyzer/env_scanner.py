"""环境变量扫描器 — 提取开发相关的环境信息"""

import platform
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

# 敏感变量名关键词（包含这些词的变量会被排除）
SENSITIVE_KEYWORDS = {
    "key",
    "token",
    "secret",
    "password",
    "passwd",
    "credential",
    "auth",
    "api_key",
    "apikey",
    "access_token",
    "private",
}

# 开发相关的环境变量名（精确匹配）
DEV_ENV_VARS = {
    "PATH",
    "PYTHONPATH",
    "PYTHONHOME",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
    "JAVA_HOME",
    "JDK_HOME",
    "JRE_HOME",
    "NODE_HOME",
    "NPM_CONFIG_PREFIX",
    "NVM_DIR",
    "GOROOT",
    "GOPATH",
    "GOBIN",
    "CARGO_HOME",
    "RUSTUP_HOME",
    "CUDA_HOME",
    "CUDA_PATH",
    "CUDNN_PATH",
    "ANDROID_HOME",
    "ANDROID_SDK_ROOT",
    "DOTNET_ROOT",
    "R_HOME",
    "HOMEBREW_PREFIX",
    "EDITOR",
    "VISUAL",
    "SHELL",
    "LANG",
    "LC_ALL",
}

# 开发相关的环境变量前缀
DEV_ENV_PREFIXES = [
    "PYENV",
    "NVM",
    "RBENV",
    "SDKMAN",
    "VCPKG",
    "CONAN",
    "npm_config",
    "PIP_",
    "VIRTUAL_ENV",
    "POETRY_VENV",
]

# 工具检测配置: (名称, 命令, 是否用stderr)
TOOL_CHECKS: list[tuple[str, list[str], bool]] = [
    ("Python", ["python", "--version"], False),
    ("Python3", ["python3", "--version"], False),
    ("Node.js", ["node", "--version"], False),
    ("npm", ["npm", "--version"], False),
    ("pnpm", ["pnpm", "--version"], False),
    ("yarn", ["yarn", "--version"], False),
    ("bun", ["bun", "--version"], False),
    ("Go", ["go", "version"], False),
    ("Rust (rustc)", ["rustc", "--version"], False),
    ("Cargo", ["cargo", "--version"], False),
    ("Java", ["java", "-version"], True),
    ("R", ["R", "--version"], False),
    ("Git", ["git", "--version"], False),
    ("Docker", ["docker", "--version"], False),
    ("uv", ["uv", "--version"], False),
    ("pip", ["pip", "--version"], False),
    ("conda", ["conda", "--version"], False),
    ("ruff", ["ruff", "--version"], False),
    ("mypy", ["mypy", "--version"], False),
]


@dataclass
class EnvInfo:
    """环境信息汇总。"""

    system: str = ""
    arch: str = ""
    shell: str = ""
    dev_env_vars: dict[str, str] = field(default_factory=dict)
    tools: list[tuple[str, str]] = field(default_factory=list)  # (name, version)
    path_entries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """返回 JSON 可序列化的环境信息。"""
        return {
            "system": self.system,
            "arch": self.arch,
            "shell": self.shell,
            "dev_env_vars": self.dev_env_vars,
            "tools": [list(item) for item in self.tools],
            "path_entries": self.path_entries,
        }


def _is_sensitive(name: str) -> bool:
    """判断环境变量是否敏感。"""
    name_lower = name.lower()
    return any(kw in name_lower for kw in SENSITIVE_KEYWORDS)


def _is_dev_related(name: str) -> bool:
    """判断环境变量是否与开发相关。"""
    if name in DEV_ENV_VARS:
        return True
    return any(name.startswith(prefix) for prefix in DEV_ENV_PREFIXES)


def _run_tool_check(tool_name: str, cmd: list[str], use_stderr: bool = False) -> tuple[str, str | None]:
    """运行工具版本检测命令，返回 (工具名, 版本字符串) 或 (工具名, None)。"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3,  # 减少超时时间从5秒到3秒
            shell=(platform.system() == "Windows"),
        )
        # 选择输出源：java -version 输出到 stderr
        output = result.stderr.strip() if use_stderr else result.stdout.strip()
        if not output:
            output = result.stdout.strip()

        if not output or result.returncode > 1:
            return tool_name, None

        first_line = output.split("\n")[0].strip()
        if not first_line or len(first_line) > 100:
            return tool_name, None

        # 排除错误信息
        lower = first_line.lower()
        if any(kw in lower for kw in ["not recognized", "not found", "no such", "error"]):
            return tool_name, None

        # 只提取版本号，pip 等工具的原始输出可能带本机安装目录。
        version = re.search(r"\b\d+(?:\.\d+)+(?:[a-zA-Z0-9.+-]*)", first_line)
        return tool_name, version.group(0) if version else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return tool_name, None


def scan_environment() -> EnvInfo:
    """只扫描平台和工具版本，不收集环境变量值或 PATH。"""
    info = EnvInfo()

    # 系统信息
    info.system = f"{platform.system()} {platform.release()}"
    info.arch = platform.machine()

    # 工具版本检测（并行执行）
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_run_tool_check, tool_name, cmd, use_stderr): (tool_name, cmd, use_stderr)
            for tool_name, cmd, use_stderr in TOOL_CHECKS
        }

        for future in as_completed(futures):
            tool_name, version = future.result()
            if version:
                info.tools.append((tool_name, version))

    info.tools.sort()
    return info
