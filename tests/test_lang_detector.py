"""语言检测器测试"""

from repoize.analyzer.lang_detector import detect_languages, get_primary_language


def test_detect_python_project(tmp_path):
    """测试 Python 项目检测。"""
    # 创建模拟的 Python 项目
    (tmp_path / "main.py").touch()
    (tmp_path / "utils.py").touch()
    (tmp_path / "models.py").touch()
    (tmp_path / "app.js").touch()

    langs = detect_languages(tmp_path)
    assert "Python" in langs
    assert langs["Python"] > langs.get("JavaScript", 0)


def test_primary_language(tmp_path):
    """测试主语言检测。"""
    (tmp_path / "main.py").touch()
    assert get_primary_language(tmp_path) == "Python"


def test_empty_project(tmp_path):
    """测试空项目。"""
    langs = detect_languages(tmp_path)
    assert len(langs) == 0
    assert get_primary_language(tmp_path) is None


def test_language_ties_are_stable_across_traversal_order(tmp_path, monkeypatch):
    import repoize.analyzer.lang_detector as detector

    paths = [tmp_path / "module.py", tmp_path / "module.ts"]
    for order in (paths, list(reversed(paths))):
        monkeypatch.setattr(detector, "_walk_files", lambda *args, order=order, **kwargs: iter(order))
        assert list(detect_languages(tmp_path).items()) == [("Python", 0.5), ("TypeScript", 0.5)]
        assert get_primary_language(tmp_path) == "Python"


def test_language_order_prioritizes_count_before_name(tmp_path, monkeypatch):
    import repoize.analyzer.lang_detector as detector

    paths = [tmp_path / "module.ts", tmp_path / "module.py", tmp_path / "other.ts", tmp_path / "module.js"]
    monkeypatch.setattr(detector, "_walk_files", lambda *args, **kwargs: iter(paths))
    assert list(detect_languages(tmp_path).items()) == [("TypeScript", 0.5), ("JavaScript", 0.25), ("Python", 0.25)]


def test_tree_case_ties_are_stable_across_directory_order(tmp_path, monkeypatch):
    from pathlib import Path

    import repoize.analyzer.project_analyzer as analyzer

    paths = [tmp_path / "a.py", tmp_path / "A.py"]
    monkeypatch.setattr(analyzer, "_is_project_entry", lambda *args: True)
    for order in (paths, list(reversed(paths))):
        monkeypatch.setattr(Path, "iterdir", lambda *args, order=order: iter(order))
        tree = analyzer._build_directory_tree(tmp_path, max_depth=1)
        assert tree.splitlines()[1:] == ["├── A.py", "└── a.py"]
