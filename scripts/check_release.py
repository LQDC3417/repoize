"""只读核对 Repoize 发布版本与产物；成功时输出版本或 SHA-256 清单。"""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def source_version(root: Path) -> str:
    """静态读取版本，不导入或执行待发布源码。"""
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]
    if project["name"] != "repoize" or not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9.!+_-]+", version):
        raise ValueError("invalid repoize project name/version")
    tree = ast.parse((root / "src/repoize/__init__.py").read_text(encoding="utf-8"))
    declarations = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
    ]
    if declarations != [version]:
        raise ValueError("source version mismatch: pyproject.toml and __version__ must agree")
    return version


def check_metadata(content: bytes, version: str) -> None:
    """拒绝错误或歧义的包名称和版本元数据。"""
    metadata = BytesParser().parsebytes(content, headersonly=True)
    if metadata.get_all("Name") != ["repoize"] or metadata.get_all("Version") != [version]:
        raise ValueError("artifact metadata name/version mismatch")


def artifact_checksums(directory: Path, version: str) -> list[str]:
    """直接读取归档，禁止解压；只接受一个 wheel 和一个源码包。"""
    wheel_name = f"repoize-{version}-py3-none-any.whl"
    sdist_name = f"repoize-{version}.tar.gz"
    expected = {wheel_name, sdist_name}
    # uv 自动写入目录标记；它与校验清单均不属于发布包。
    found = {path.name for path in directory.iterdir() if path.name not in {"SHA256SUMS", ".gitignore"}}
    if found != expected or any(not (directory / name).is_file() for name in expected):
        raise ValueError(f"artifacts must be exactly {sorted(expected)}; found {sorted(found)}")

    with zipfile.ZipFile(directory / wheel_name) as wheel:
        metadata_path = f"repoize-{version}.dist-info/METADATA"
        metadata_files = [name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")]
        if metadata_files != [metadata_path]:
            raise ValueError("wheel metadata path is missing, duplicated, or inconsistent")
        check_metadata(wheel.read(metadata_path), version)

    with tarfile.open(directory / sdist_name, "r:gz") as sdist:
        metadata_path = f"repoize-{version}/PKG-INFO"
        members = [member for member in sdist.getmembers() if member.name == metadata_path]
        if len(members) != 1 or not members[0].isfile():
            raise ValueError("sdist metadata path is missing, duplicated, or not a regular file")
        content = sdist.extractfile(members[0])
        if content is None:
            raise ValueError("sdist metadata cannot be read")
        with content:
            check_metadata(content.read(), version)

    return [f"{hashlib.sha256((directory / name).read_bytes()).hexdigest()}  {name}" for name in sorted(expected)]


def main() -> int:
    """检查失败使用非零状态和简洁错误，不生成部分校验清单。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="source checkout (default: current directory)")
    parser.add_argument("--dist", type=Path, help="directory containing the wheel and sdist")
    parser.add_argument("--tag", help="optional release tag; must equal v{source version}")
    args = parser.parse_args()
    try:
        version = source_version(args.root)
        if args.tag is not None and args.tag != f"v{version}":
            raise ValueError(f"tag must be v{version}, got {args.tag!r}")
        output = artifact_checksums(args.dist, version) if args.dist is not None else [version]
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        SyntaxError,
        tarfile.TarError,
        zipfile.BadZipFile,
        EOFError,
    ) as exc:
        print(f"release check failed: {exc}", file=sys.stderr)
        return 1
    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
