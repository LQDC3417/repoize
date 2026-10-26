"""从仓库外运行已安装 CLI，核验入口、模板、Schema 和重复更新。"""

import json
import os
import subprocess
import sysconfig
import tempfile
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import jsonschema

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
        preview = json.loads(run("init", "--dry-run", "--format", "json").stdout)
        schema = json.loads(files("repoize").joinpath("schemas/changes.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(preview, schema)
        assert preview["summary"]["create"] == 1
        assert not (project / "AGENTS.md").exists()
        run("init")
        run("update", "--check")
        assert (project / "AGENTS.md").is_file()
        assert all(not (project / name).exists() for name in OUTPUT_FILES[1:])
        run(
            "init",
            "--type",
            "claude",
            "--type",
            "cursor",
            "--type",
            "cursorrules",
            "--type",
            "copilot",
            "--type",
            "mcp",
            "--type",
            "skill",
        )
        assert all((project / name).is_file() for name in OUTPUT_FILES)
        run("update", "--check")
        doctor = json.loads(run("doctor", "--format", "json").stdout)
        doctor_schema = json.loads(files("repoize").joinpath("schemas/doctor.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(doctor, doctor_schema)
        assert doctor["summary"]["errors"] == 0
        checked = json.loads(run("update", "--check", "--format", "json").stdout)
        jsonschema.validate(checked, schema)
        assert next(change for change in checked["changes"] if change["type"] == "mcp")["reason"] == "not_comparable"
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
        run("update", "--check")
        run("update", "--no-env")
        before = {name: (project / name).read_bytes() for name in OUTPUT_FILES}
        run("update", "--no-env")
        assert before == {name: (project / name).read_bytes() for name in OUTPUT_FILES}
        assert agents.read_bytes().startswith(prefix)
        assert agents.read_bytes().endswith(suffix)
        (project / "new-module.py").write_text("pass\n", encoding="utf-8")
        drift = subprocess.run(
            [str(cli), "update", "--check", "--format", "json"],
            cwd=project,
            env=env,
            encoding="utf-8",
            capture_output=True,
        )
        assert drift.returncode == 1, drift.stderr
        assert json.loads(drift.stdout)["summary"]["update"] > 0
        run("update")
        run("update", "--check")

    print("Installed package smoke checks passed.")


if __name__ == "__main__":
    main()
