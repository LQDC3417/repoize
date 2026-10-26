"""发布前核对源码声明、标签和同批构建产物。"""

import hashlib
import io
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parents[1] / "scripts/check_release.py"


@pytest.fixture
def release_tree(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "repoize"\nversion = "0.3.0"\n', encoding="utf-8")
    package = tmp_path / "src/repoize"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "0.3.0"\n', encoding="utf-8")
    artifacts = tmp_path / "dist"
    artifacts.mkdir()
    write_artifacts(artifacts)
    return tmp_path


def write_artifacts(path, *, wheel_version="0.3.0", sdist_version="0.3.0", name="repoize"):
    with zipfile.ZipFile(path / "repoize-0.3.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr(
            "repoize-0.3.0.dist-info/METADATA", f"Metadata-Version: 2.3\nName: {name}\nVersion: {wheel_version}\n"
        )
    metadata = f"Metadata-Version: 2.3\nName: {name}\nVersion: {sdist_version}\n".encode()
    with tarfile.open(path / "repoize-0.3.0.tar.gz", "w:gz") as sdist:
        entry = tarfile.TarInfo("repoize-0.3.0/PKG-INFO")
        entry.size = len(metadata)
        sdist.addfile(entry, io.BytesIO(metadata))


def run_check(root, *args):
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), *args], capture_output=True, text=True, encoding="utf-8"
    )


def test_release_checks_matching_batch_and_prints_sha256(release_tree):
    result = run_check(release_tree, "--dist", str(release_tree / "dist"), "--tag", "v0.3.0")
    assert result.returncode == 0, result.stderr
    expected = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}"
        for path in sorted((release_tree / "dist").iterdir())
    ]
    assert result.stdout.splitlines() == expected


def test_release_reads_version_without_executing_source(release_tree):
    marker = release_tree / "executed"
    (release_tree / "src/repoize/__init__.py").write_text(
        f'raise RuntimeError({str(marker)!r})\n__version__ = "0.3.0"\n', encoding="utf-8"
    )
    result = run_check(release_tree)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "0.3.0\n"
    assert not marker.exists()


@pytest.mark.parametrize("tag", ["v0.2.0", "0.3.0", "v0.3.0-rc1"])
def test_release_rejects_wrong_tag(release_tree, tag):
    result = run_check(release_tree, "--tag", tag)
    assert result.returncode == 1
    assert "tag" in result.stderr


def test_release_rejects_source_version_mismatch(release_tree):
    (release_tree / "src/repoize/__init__.py").write_text('__version__ = "0.2.0"\n', encoding="utf-8")
    result = run_check(release_tree)
    assert result.returncode == 1
    assert "version" in result.stderr


@pytest.mark.parametrize("missing", ["repoize-0.3.0.tar.gz", "repoize-0.3.0-py3-none-any.whl"])
def test_release_rejects_missing_artifact(release_tree, missing):
    (release_tree / "dist" / missing).unlink()
    result = run_check(release_tree, "--dist", str(release_tree / "dist"))
    assert result.returncode == 1
    assert "artifacts" in result.stderr


def test_release_rejects_extra_artifact(release_tree):
    (release_tree / "dist/repoize-0.2.0.tar.gz").write_bytes(b"old")
    result = run_check(release_tree, "--dist", str(release_tree / "dist"))
    assert result.returncode == 1
    assert "artifacts" in result.stderr


@pytest.mark.parametrize("wrong", [{"wheel_version": "0.2.0"}, {"sdist_version": "0.2.0"}, {"name": "other"}])
def test_release_rejects_inconsistent_metadata(release_tree, wrong):
    write_artifacts(release_tree / "dist", **wrong)
    result = run_check(release_tree, "--dist", str(release_tree / "dist"))
    assert result.returncode == 1
    assert "metadata" in result.stderr


def test_release_rejects_corrupt_archive_without_traceback(release_tree):
    (release_tree / "dist/repoize-0.3.0.tar.gz").write_bytes(b"not a tarball")
    result = run_check(release_tree, "--dist", str(release_tree / "dist"))
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_release_allows_checksum_output_in_artifact_directory(release_tree):
    (release_tree / "dist/SHA256SUMS").touch()
    result = run_check(release_tree, "--dist", str(release_tree / "dist"))
    assert result.returncode == 0, result.stderr
    assert "SHA256SUMS" not in result.stdout


def test_release_allows_uv_build_directory_marker(release_tree):
    (release_tree / "dist/.gitignore").write_text("*\n", encoding="utf-8")
    result = run_check(release_tree, "--dist", str(release_tree / "dist"))
    assert result.returncode == 0, result.stderr
    assert ".gitignore" not in result.stdout
