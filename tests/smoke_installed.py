"""从仓库外运行已安装 CLI，核验入口、模板、Schema 和重复更新。"""

import json
import os
import subprocess
import sysconfig
import tempfile
from importlib.metadata import version
from pathlib import Path

OUTPUT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".cursor/rules/repoize.mdc",
    ".github/copilot-instructions.md",
    ".mcp.json",
    ".claude/skills/project-dev/SKILL.md",
)


def main() -> None:
    """验证安装包的完整使用流程，失败时保留子进程错误信息。"""
    cli = Path(sysconfig.get_path("scripts")) / ("repoize.exe" if os.name == "nt" else "repoize")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "utf-8"

    with tempfile.TemporaryDirectory(prefix="repoize-smoke-") as temp:
        project = Path(temp) / "示例[project]"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            "[project]\nname = 'smoke-app'\ndependencies = ['click>=8', 'rich>=13']\n"
            "[project.scripts]\nsmoke-app = 'app:main'\n",
            encoding="utf-8",
        )
        (project / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")

        def run(*args: str) -> subprocess.CompletedProcess:
            """子进程只使用安装环境，防止源码路径掩盖包资源缺失。"""
            return subprocess.run(
                [str(cli), *args], cwd=project, env=env, encoding="utf-8", capture_output=True, check=True
            )

        assert run("--version").stdout.strip().endswith(version("repoize"))
        run("init")
        assert all((project / name).is_file() for name in OUTPUT_FILES)
        assert json.loads((project / ".mcp.json").read_text(encoding="utf-8")) == {"mcpServers": {}}
        assert not (project / ".claude/mcp.json").exists()
        assert not (project / ".cursorrules").exists()
        for name in (".cursor/rules/repoize.mdc", ".claude/skills/project-dev/SKILL.md"):
            content = (project / name).read_text(encoding="utf-8")
            assert content.startswith("---\n")
            assert content.index("---", 3) < content.index("<!-- repoize:generated-start -->")
        assert "name: project-dev\n" in (project / ".claude/skills/project-dev/SKILL.md").read_text(encoding="utf-8")

        result = run("analyze", "--format", "json", "--no-env")
        data = json.loads(result.stdout)
        assert data["project_name"] == project.name
        assert {dep["name"] for dep in data["dependencies"]} == {"click", "rich"}
        assert data["commands"]["run"] == ["smoke-app"]
        report = Path(temp) / "analysis.json"
        report.write_text(result.stdout, encoding="utf-8")
        run("validate", str(report))

        agents = project / "AGENTS.md"
        prefix = "# 手写前言\n".encode()
        suffix = "\n# 手写尾部\n".encode()
        agents.write_bytes(prefix + agents.read_bytes() + suffix)
        # 第一次更新纳入新生成的目录；第二次应不再改变文件。
        run("update", "--no-env")
        before = {name: (project / name).read_bytes() for name in OUTPUT_FILES}
        run("update", "--no-env")
        assert before == {name: (project / name).read_bytes() for name in OUTPUT_FILES}
        assert agents.read_bytes().startswith(prefix)
        assert agents.read_bytes().endswith(suffix)

    print("Installed package smoke checks passed.")


if __name__ == "__main__":
    main()
