"""生成器测试"""

import json
import tempfile
from pathlib import Path

import pytest

from repoize.analyzer.project_analyzer import analyze_project
from repoize.generator.agents_md import AgentsMdGenerator
from repoize.generator.claude_md import ClaudeMdGenerator
from repoize.generator.copilot import CopilotGenerator
from repoize.generator.cursorrules import CursorRulesGenerator
from repoize.generator.mcp_config import McpConfigGenerator
from repoize.generator.skill_md import SkillMdGenerator


def _make_analysis():
    """创建测试用的分析结果。"""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp / "pyproject.toml").write_text(
        """[project]
name = "test-project"
dependencies = ["fastapi>=0.100", "uvicorn"]
[project.optional-dependencies]
dev = ["pytest"]
[project.scripts]
test-app = "app.main:main"
""",
        encoding="utf-8",
    )
    (tmp / "tests").mkdir()
    (tmp / "tests" / "test_main.py").write_text("def test_ok(): pass", encoding="utf-8")
    return analyze_project(tmp, scan_env=False)


def test_agents_md_generator():
    """测试 AGENTS.md 生成器。"""
    analysis = _make_analysis()
    gen = AgentsMdGenerator(analysis)
    content = gen.generate()
    assert analysis.project_name in content
    assert "Python" in content
    assert "fastapi" in content
    assert "pytest" in content
    assert gen.output_filename == "AGENTS.md"


def test_claude_md_generator():
    """测试 CLAUDE.md 生成器。"""
    analysis = _make_analysis()
    gen = ClaudeMdGenerator(analysis)
    content = gen.generate()
    assert "Claude Code" in content
    assert analysis.project_name in content
    assert "Python" in content
    assert "fastapi" in content
    assert "编码规范" in content
    assert "工作流程" in content
    assert gen.output_filename == "CLAUDE.md"


def test_cursorrules_generator():
    """测试 .cursorrules 生成器。"""
    analysis = _make_analysis()
    gen = CursorRulesGenerator(analysis)
    content = gen.generate()
    assert "Cursor Rules" in content
    assert "pytest" in content
    assert gen.output_filename == ".cursorrules"


def test_copilot_generator():
    """测试 copilot-instructions 生成器。"""
    analysis = _make_analysis()
    gen = CopilotGenerator(analysis)
    content = gen.generate()
    assert "Copilot" in content
    assert gen.output_filename == ".github/copilot-instructions.md"


def test_mcp_config_generator():
    """测试 MCP 配置生成器。"""
    analysis = _make_analysis()
    gen = McpConfigGenerator(analysis)
    content = gen.generate()
    assert "mcpServers" in content
    assert "git" in content
    assert gen.output_filename == ".claude/mcp.json"


def test_skill_md_generator():
    """测试 SKILL.md 生成器。"""
    analysis = _make_analysis()
    gen = SkillMdGenerator(analysis)
    content = gen.generate()
    assert analysis.project_name in content
    assert gen.output_filename == ".claude/skills/project-dev/SKILL.md"


def test_generator_write(tmp_path):
    """测试生成器写入文件。"""
    analysis = _make_analysis()
    gen = AgentsMdGenerator(analysis)
    result_path = gen.write(tmp_path)
    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert analysis.project_name in content


def test_generator_write_conflict(tmp_path):
    """测试生成器文件冲突检测。"""
    analysis = _make_analysis()
    gen = AgentsMdGenerator(analysis)
    gen.write(tmp_path)

    with pytest.raises(FileExistsError):
        gen.write(tmp_path, force=False)


def test_generator_write_force(tmp_path):
    """测试 --force 覆盖写入。"""
    analysis = _make_analysis()
    gen = AgentsMdGenerator(analysis)
    gen.write(tmp_path)
    gen.write(tmp_path, force=True)


def test_dep_parser_no_scripts():
    """测试依赖解析不包含 scripts 条目。"""
    analysis = _make_analysis()
    dep_names = [d.name for d in analysis.dependencies]
    # app.main:main 是 scripts 条目，不应出现在依赖中
    assert "app.main:main" not in dep_names
    assert "fastapi" in dep_names
    assert "uvicorn" in dep_names
    assert "pytest" in dep_names


def test_template_no_bom():
    """测试模板文件不含 BOM。"""
    from jinja2 import Environment, FileSystemLoader

    template_dir = Path(__file__).parent.parent / "src" / "repoize" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    for name in ["agents_md.j2", "claude_md.j2", "cursorrules.j2", "copilot.j2", "mcp_config.j2", "skill_md.j2"]:
        source, _, _ = env.loader.get_source(env, name)
        assert not source.startswith("\ufeff"), f"{name} contains BOM"


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "languages"

ALL_GENERATORS = [
    AgentsMdGenerator,
    ClaudeMdGenerator,
    CursorRulesGenerator,
    CopilotGenerator,
    SkillMdGenerator,
]


@pytest.mark.parametrize(
    ("language", "setup", "test_cmd"),
    [
        ("javascript", "npm install", "npm run test"),
        ("typescript", "npm install", "npm run test"),
        ("go", "go mod download", "go test ./..."),
        ("rust", "cargo build", "cargo test"),
        ("java", "mvn -q dependency:resolve", "mvn test"),
        ("ruby", "bundle install", "bundle exec rake test"),
        ("php", "composer install", "composer run test"),
    ],
)
def test_non_python_generator_outputs(language, setup, test_cmd):
    """测试非 Python 项目生成语言正确的配置。"""
    fixture = FIXTURE_ROOT / language
    analysis = analyze_project(fixture, scan_env=False)
    assert analysis.profile is not None
    for generator_cls in ALL_GENERATORS:
        content = generator_cls(analysis).generate()
        assert setup in content
        assert test_cmd in content
        assert "pip install" not in content


def test_python_generator_keeps_python_setup():
    """测试 Python 项目仍保留现有安装方式。"""
    analysis = _make_analysis()
    content = AgentsMdGenerator(analysis).generate()
    assert 'pip install -e ".[dev]"' in content


def test_mcp_config_is_generic_for_non_python():
    """测试非 Python 项目也生成通用 MCP 配置。"""
    fixture = FIXTURE_ROOT / "go"
    analysis = analyze_project(fixture, scan_env=False)
    content = McpConfigGenerator(analysis).generate()
    assert "mcpServers" in content
    assert "filesystem" in content


def test_generator_write_adds_markers(tmp_path):
    """测试文本生成文件包含 managed marker。"""
    analysis = _make_analysis()
    output_path = AgentsMdGenerator(analysis).write(tmp_path)
    content = output_path.read_text(encoding="utf-8")
    assert "<!-- repoize:generated-start -->" in content
    assert "<!-- repoize:generated-end -->" in content


def test_generator_update_preserves_manual_content(tmp_path):
    """测试增量更新保留 marker 外的手写内容。"""
    analysis = _make_analysis()
    gen = AgentsMdGenerator(analysis)
    output_path = gen.write(tmp_path)
    manual = "\n# 手写内容\n"
    output_path.write_text(output_path.read_text(encoding="utf-8") + manual, encoding="utf-8")

    gen.update(tmp_path)

    content = output_path.read_text(encoding="utf-8")
    assert manual in content
    assert "pytest" in content


def test_generator_update_without_markers_skips(tmp_path):
    """测试没有 managed marker 的已有文件不会被覆盖。"""
    analysis = _make_analysis()
    output_path = tmp_path / "AGENTS.md"
    output_path.write_text("# 用户文件", encoding="utf-8")

    result = AgentsMdGenerator(analysis).update(tmp_path)

    assert result is None
    assert output_path.read_text(encoding="utf-8") == "# 用户文件"


def test_mcp_update_preserves_extra_servers(tmp_path):
    """测试 JSON 更新保留用户自定义 MCP server。"""
    analysis = _make_analysis()
    output_path = tmp_path / ".claude" / "mcp.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"mcpServers": {"custom": {"command": "echo", "args": []}}}),
        encoding="utf-8",
    )

    McpConfigGenerator(analysis).update(tmp_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "custom" in data["mcpServers"]
    assert "git" in data["mcpServers"]
    assert "filesystem" in data["mcpServers"]


def test_agents_md_contains_dynamic_directory_tree(tmp_path):
    """测试 AGENTS.md 包含动态生成的目录树，而非硬编码内容。"""
    (tmp_path / "main.py").write_text("print('hi')", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("pass", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("pass", encoding="utf-8")

    analysis = analyze_project(tmp_path, scan_env=False)
    content = AgentsMdGenerator(analysis).generate()

    # 应包含真实目录名
    assert "main.py" in content
    assert "src/" in content
    assert "tests/" in content
    # 不应包含旧的硬编码注释
    assert "# 源代码" not in content


def test_directory_tree_skips_ignored_dirs(tmp_path):
    """测试目录树跳过 __pycache__ 等忽略目录。"""
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cache.pyc").write_bytes(b"")
    (tmp_path / ".git").mkdir()

    analysis = analyze_project(tmp_path, scan_env=False)
    tree = analysis.directory_tree

    assert "__pycache__" not in tree
    assert ".git" not in tree


def test_mcp_deep_merge_preserves_nested_config(tmp_path):
    """测试 MCP JSON 更新时递归合并嵌套配置。"""
    analysis = _make_analysis()
    output_path = tmp_path / ".claude" / "mcp.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 用户自定义了一个带嵌套 env 的 server
    user_config = {
        "mcpServers": {
            "git": {
                "command": "uvx",
                "args": ["mcp-server-git", "--repository", "/custom/path"],
                "env": {"GIT_DIR": "/custom/.git"},
            }
        }
    }
    output_path.write_text(
        json.dumps(user_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    McpConfigGenerator(analysis).update(tmp_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    # 用户的嵌套 env 应被保留
    assert data["mcpServers"]["git"]["env"]["GIT_DIR"] == "/custom/.git"
    # 同名字段优先保留已有值，避免覆盖用户修改。
    assert data["mcpServers"]["git"]["args"] == user_config["mcpServers"]["git"]["args"]
    # 模板新生成的 filesystem server 应被添加
    assert "filesystem" in data["mcpServers"]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("suffix", ["", "\n\n# 手写尾部\n"])
def test_text_update_is_idempotent_and_preserves_manual_bytes(tmp_path, newline, suffix):
    """重复更新不新增空行，区间外内容与换行保持不变。"""
    gen = AgentsMdGenerator(_make_analysis())
    prefix = "# 手写前言\n\n".replace("\n", newline)
    suffix = suffix.replace("\n", newline)
    managed = gen.generate_marked().removesuffix("\n").replace("\n", newline)
    original = (prefix + managed + suffix).encode("utf-8")
    output_path = tmp_path / gen.output_filename
    output_path.write_bytes(original)

    for _ in range(2):
        gen.update(tmp_path)
        assert output_path.read_bytes() == original


def test_mcp_update_preserves_conflicting_user_values_and_warns(tmp_path, caplog):
    """MCP 更新保留手写启动命令和参数，并提示冲突。"""
    gen = McpConfigGenerator(_make_analysis())
    output_path = tmp_path / gen.output_filename
    output_path.parent.mkdir(parents=True)
    original = {"mcpServers": {"git": {"command": "custom-git", "args": ["--custom"]}}}
    output_path.write_text(json.dumps(original), encoding="utf-8")

    gen.update(tmp_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["mcpServers"]["git"] == original["mcpServers"]["git"]
    assert "filesystem" in data["mcpServers"]
    assert "保留已有值" in caplog.text


@pytest.mark.parametrize("content", ["{invalid", "[]", "null"])
def test_mcp_update_rejects_invalid_configuration_without_overwriting(tmp_path, content):
    """无效 JSON 不应被当作未管理文件跳过，也不能被覆盖。"""
    gen = McpConfigGenerator(_make_analysis())
    output_path = tmp_path / gen.output_filename
    output_path.parent.mkdir(parents=True)
    output_path.write_text(content, encoding="utf-8")
    original = output_path.read_bytes()

    with pytest.raises(ValueError):
        gen.update(tmp_path)

    assert output_path.read_bytes() == original


def test_text_update_propagates_read_errors(tmp_path):
    """读取失败必须交给调用方报告，而非伪装成缺少 marker。"""
    gen = AgentsMdGenerator(_make_analysis())
    (tmp_path / gen.output_filename).mkdir()

    with pytest.raises(OSError):
        gen.update(tmp_path)


def test_agents_md_contains_run_commands(tmp_path):
    """测试 AGENTS.md 包含 run 命令（如 npm start）。"""
    pkg = {
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js",
            "test": "jest",
        },
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    (tmp_path / "index.js").write_text("console.log('hi')", encoding="utf-8")

    analysis = analyze_project(tmp_path, scan_env=False)
    content = AgentsMdGenerator(analysis).generate()

    assert "npm run start" in content or "npm run dev" in content
