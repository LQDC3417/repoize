"""环境变量扫描器测试"""

from repoize.analyzer.env_scanner import (
    EnvInfo,
    _is_dev_related,
    _is_sensitive,
    scan_environment,
)


def test_is_sensitive():
    """测试敏感变量检测。"""
    assert _is_sensitive("AWS_SECRET_ACCESS_KEY") is True
    assert _is_sensitive("GITHUB_TOKEN") is True
    assert _is_sensitive("API_KEY") is True
    assert _is_sensitive("DATABASE_PASSWORD") is True
    assert _is_sensitive("MY_PRIVATE_KEY") is True
    assert _is_sensitive("PATH") is False
    assert _is_sensitive("PYTHONHOME") is False
    assert _is_sensitive("CUDA_HOME") is False


def test_is_dev_related():
    """测试开发相关变量检测。"""
    assert _is_dev_related("PATH") is True
    assert _is_dev_related("PYTHONPATH") is True
    assert _is_dev_related("JAVA_HOME") is True
    assert _is_dev_related("CUDA_HOME") is True
    assert _is_dev_related("GOPATH") is True
    assert _is_dev_related("CARGO_HOME") is True
    assert _is_dev_related("VIRTUAL_ENV") is True
    assert _is_dev_related("CONDA_PREFIX") is True
    # 非开发相关
    assert _is_dev_related("COMPUTERNAME") is False
    assert _is_dev_related("TEMP") is False
    assert _is_dev_related("USERPROFILE") is False


def test_scan_environment():
    """测试环境扫描返回完整结果。"""
    info = scan_environment()
    assert isinstance(info, EnvInfo)
    assert info.system  # 应有系统信息
    assert info.arch  # 应有架构信息
    assert info.dev_env_vars == {}
    assert info.shell == ""
    assert info.tools == sorted(info.tools)


def test_scan_environment_tools():
    """测试工具检测至少能找到 Python。"""
    info = scan_environment()
    tool_names = [name for name, _ in info.tools]
    assert "Python" in tool_names or "Python3" in tool_names


def test_env_info_path_entries():
    """环境摘要不收集 PATH 条目。"""
    info = scan_environment()
    assert info.path_entries == []
