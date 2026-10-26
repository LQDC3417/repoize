"""独立执行和根仓库收集均不依赖导入路径。"""

import runpy
from pathlib import Path


def test_greeting():
    app = runpy.run_path(str(Path(__file__).resolve().parents[1] / "app.py"))
    assert app["greet"]() == "Hello, world!"
    assert app["greet"]("Repoize") == "Hello, Repoize!"
