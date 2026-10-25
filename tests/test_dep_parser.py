"""依赖解析器测试"""

from pathlib import Path

import pytest

from repoize.analyzer.dep_parser import parse_dependencies
from repoize.analyzer.language_profiles import get_language_profile


def test_pyproject_toml_literals_extras_and_comments(tmp_path):
    """保留数组里的真实依赖，忽略注释并识别各种需求写法。"""
    content = """[project] # 项目配置
dependencies = [
    'requests[socks]>=2.0', # "comment-package"
    'importlib-metadata; python_version < "3.11"',
    "demo-pkg @ https://example.com/demo.whl#sha256=abc",
    "rich>=13.0",
]
[project.optional-dependencies] # 所有可选组沿用开发依赖分类
test = ['pytest>=7', 'pytest-cov']
docs = ['sphinx']
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8-sig")
    deps = parse_dependencies(tmp_path)
    assert [(dep.name, dep.dev, dep.version_spec) for dep in deps] == [
        ("requests", False, ""),
        ("importlib-metadata", False, ""),
        ("demo-pkg", False, ""),
        ("rich", False, ""),
        ("pytest", True, ""),
        ("pytest-cov", True, ""),
        ("sphinx", True, ""),
    ]


@pytest.mark.parametrize(
    "content",
    [
        '[project]\ndependencies = ["click"',
        'project = "invalid"',
        '[project]\ndependencies = "click"\noptional-dependencies = 3',
        '[project]\ndependencies = [42, {name = "click"}]\noptional-dependencies = {dev = "pytest"}',
        '[project]\ndependencies = []\n[project.optional-dependencies]\ndev = {name = "pytest"}',
    ],
)
def test_pyproject_invalid_toml_or_dependency_shapes(tmp_path, content):
    """语法错误或错误类型应安全忽略。"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    assert parse_dependencies(tmp_path) == []


@pytest.mark.parametrize("content", [None, b"\xff\xfe"])
def test_pyproject_unreadable_input(tmp_path, content):
    """目录和非 UTF-8 文件不能中断分析。"""
    path = tmp_path / "pyproject.toml"
    if content is None:
        path.mkdir()
    else:
        path.write_bytes(content)
    assert parse_dependencies(tmp_path) == []


def test_pyproject_permission_error(tmp_path, monkeypatch):
    """文件存在但读取被拒绝时返回空依赖。"""
    (tmp_path / "pyproject.toml").write_text("[project]", encoding="utf-8")

    def denied_read(*args, **kwargs):
        raise PermissionError("拒绝读取")

    monkeypatch.setattr(Path, "read_text", denied_read)
    assert parse_dependencies(tmp_path) == []


def test_parse_pyproject(tmp_path):
    """测试 pyproject.toml 解析。"""
    content = """[project]
name = "test"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
]
"""
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")
    deps = parse_dependencies(tmp_path)

    names = [d.name for d in deps]
    assert "click" in names
    assert "rich" in names
    assert "pytest" in names

    pytest_dep = next(d for d in deps if d.name == "pytest")
    assert pytest_dep.dev is True


def test_parse_requirements(tmp_path):
    """测试 requirements.txt 解析。"""
    content = """click>=8.0
rich>=13.0
# comment
-e git+https://...
"""
    (tmp_path / "requirements.txt").write_text(content, encoding="utf-8")
    deps = parse_dependencies(tmp_path)

    names = [d.name for d in deps]
    assert "click" in names
    assert "rich" in names


def test_parse_pom_xml(tmp_path):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <artifactId>junit</artifactId>
      <version>4.13.2</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
"""
    (tmp_path / "pom.xml").write_text(content, encoding="utf-8")
    deps = parse_dependencies(tmp_path, profile=get_language_profile("Java"))
    names = [d.name for d in deps]
    assert "org.springframework.boot:spring-boot-starter-web" in names
    assert "junit" in names


def test_parse_gradle_build(tmp_path):
    content = """dependencies {
    implementation 'com.google.guava:guava:33.0.0-jre'
    api "org.slf4j:slf4j-api:2.0.13"
    testImplementation 'junit:junit:4.13.2'
}
"""
    (tmp_path / "build.gradle").write_text(content, encoding="utf-8")
    deps = parse_dependencies(tmp_path, profile=get_language_profile("Java"))
    names = [d.name for d in deps]
    assert "com.google.guava:guava" in names
    assert "org.slf4j:slf4j-api" in names


def test_parse_gemfile(tmp_path):
    content = """source "https://rubygems.org"
gem "rails", "~> 7.0"
gem "puma"
"""
    (tmp_path / "Gemfile").write_text(content, encoding="utf-8")
    deps = parse_dependencies(tmp_path, profile=get_language_profile("Ruby"))
    names = [d.name for d in deps]
    assert "rails" in names
    assert "puma" in names


def test_parse_composer_json(tmp_path):
    content = """{
  "require": {
    "laravel/framework": "^11.0"
  },
  "require-dev": {
    "phpunit/phpunit": "^11.0"
  }
}
"""
    (tmp_path / "composer.json").write_text(content, encoding="utf-8")
    deps = parse_dependencies(tmp_path, profile=get_language_profile("PHP"))
    phpunit = next(d for d in deps if d.name == "phpunit/phpunit")
    assert phpunit.dev is True
