"""兼容 Python 3.10 的安全 TOML 读取。"""

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_toml(filepath: Path) -> dict[str, Any]:
    """读取可选 BOM 的 UTF-8 TOML；文件不可读或语法错误时返回空表。"""
    try:
        return tomllib.loads(filepath.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {}
