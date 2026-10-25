import pytest

from repoize.analyzer.cmd_extractor import extract_commands
from repoize.analyzer.language_profiles import get_language_profile


def test_pyproject_registered_script_names_and_inline_tools(tmp_path):
    """入口命令使用注册名，内联工具表也应被识别。"""
    content = """[project.scripts] # 命令入口
"my-cli" = 'package.cli:main'
[tool]
ruff = {line-length = 88}
mypy = {strict = true}
flake8 = {}
black = {}
isort = {}
pytest = {ini_options = {testpaths = ['tests']}}
[tool.poetry.scripts]
other-cli = "other:main"
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8-sig")
    cmds = extract_commands(tmp_path)
    assert cmds.run == ["my-cli", "other-cli"]
    assert cmds.test == ["pytest"]
    assert cmds.lint == ["ruff check .", "mypy .", "flake8 ."]
    assert cmds.format == ["ruff format .", "black .", "isort ."]


def test_pyproject_comment_tools_do_not_create_commands(tmp_path):
    """注释和描述中的工具名称不是工具配置。"""
    content = """# [tool.ruff]
# [tool.mypy]
[project]
description = "pytest and testpaths are described here"
dependencies = ['pytest-cov']
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    assert extract_commands(tmp_path).to_dict() == {
        "build": [],
        "test": [],
        "lint": [],
        "format": [],
        "run": [],
    }


def test_poetry_structured_console_script(tmp_path):
    """Poetry 的结构化 console script 同样使用注册名。"""
    content = """[tool.poetry.scripts]
my-cli = {reference = "package.cli:main", type = "console"}
invalid-cli = 42
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    assert extract_commands(tmp_path).run == ["my-cli"]


@pytest.mark.parametrize(
    "section",
    [
        "[project]\ndependencies = ['pytest>=7']",
        "[project.optional-dependencies]\ntest = ['pytest>=7']",
        "[tool.poetry.dependencies]\npytest = '^7'",
        "[tool.poetry.dev-dependencies]\npytest = '^7'",
        "[tool.poetry.group.test.dependencies]\npytest = '^7'",
    ],
)
def test_pyproject_pytest_dependency_detection(tmp_path, section):
    """测试命令仍能从依赖声明识别。"""
    (tmp_path / "pyproject.toml").write_text(section, encoding="utf-8")
    assert extract_commands(tmp_path).test == ["pytest"]


@pytest.mark.parametrize(
    "content",
    [
        '[project.scripts]\nbroken-cli = "demo:main"\n[invalid',
        'project = "invalid"\ntool = ["ruff"]',
        '[project]\nscripts = ["invalid"]\n[tool]\npoetry = 42\nruff = "invalid"',
    ],
)
def test_pyproject_invalid_toml_and_shapes_create_no_commands(tmp_path, content):
    """无效 TOML 和错误类型不应生成猜测命令。"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    assert not any(extract_commands(tmp_path).to_dict().values())


def test_go_profile_fills_default_commands(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com/foo\n\ngo 1.22\n", encoding="utf-8")
    cmds = extract_commands(tmp_path, profile=get_language_profile("Go"))
    assert "go build ./..." in cmds.build
    assert "go test ./..." in cmds.test
    assert "gofmt -w ." in cmds.format


def test_package_scripts_take_priority(tmp_path):
    content = """{
  "scripts": {
    "build": "vite build",
    "test": "vitest run",
    "lint": "eslint ."
  }
}
"""
    (tmp_path / "package.json").write_text(content, encoding="utf-8")
    cmds = extract_commands(tmp_path, profile=get_language_profile("JavaScript"))
    assert "npm run build" in cmds.build
    assert "npm run lint" in cmds.lint


def test_java_maven_commands(tmp_path):
    (tmp_path / "pom.xml").write_text("<project></project>", encoding="utf-8")
    cmds = extract_commands(tmp_path, profile=get_language_profile("Java"))
    assert "mvn verify" in cmds.build
    assert "mvn test" in cmds.test


def test_php_composer_scripts(tmp_path):
    content = """{
  "scripts": {
    "test": "phpunit",
    "lint": "php-cs-fixer check"
  }
}
"""
    (tmp_path / "composer.json").write_text(content, encoding="utf-8")
    cmds = extract_commands(tmp_path, profile=get_language_profile("PHP"))
    assert "composer run test" in cmds.test
    assert "composer run lint" in cmds.lint
