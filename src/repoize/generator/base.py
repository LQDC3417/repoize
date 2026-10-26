"""生成器基类。"""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from ..analyzer.project_analyzer import ProjectAnalysis
from ..formats import GENERATED_END, GENERATED_START, marker_bounds, split_frontmatter
from ..targets import legacy_decision, safe_output_path

GENERATED_BANNER = "<!-- 本文件由 repoize 自动生成；可修改生成区间之外的内容。 -->"


class BaseGenerator(ABC):
    """配置文件生成器基类。"""

    def __init__(self, analysis: ProjectAnalysis):
        """初始化生成器。"""
        self.analysis = analysis

    @property
    @abstractmethod
    def name(self) -> str:
        """生成器名称。"""
        ...

    @property
    @abstractmethod
    def output_filename(self) -> str:
        """相对项目根目录的输出文件名。"""
        ...

    @property
    def is_json(self) -> bool:
        """判断输出是否为 JSON。"""
        return self.output_filename.endswith(".json")

    @abstractmethod
    def generate(self) -> str:
        """渲染完整文件（不含 managed marker）。"""
        ...

    def generate_body(self) -> str:
        """渲染可管理正文，头部只在创建完整文件时写入。"""
        return split_frontmatter(self.generate(), self.output_filename)[1].strip()

    def generate_marked_body(self) -> str:
        """为正文添加生成标记。"""
        return f"{GENERATED_START}\n{GENERATED_BANNER}\n{self.generate_body()}\n{GENERATED_END}\n"

    def generate_marked(self) -> str:
        """渲染完整文件，frontmatter 始终位于第一行。"""
        header, _ = split_frontmatter(self.generate(), self.output_filename)
        return header + self.generate_marked_body()

    def validate_existing(self, output_path: Path) -> None:
        """已有文件即使将跳过，也不能隐藏损坏标记或旧 Skill 格式。"""
        if not output_path.exists():
            return
        content = output_path.read_bytes().decode("utf-8")
        if self.is_json:
            if not isinstance(json.loads(content.removeprefix("\ufeff")), dict):
                raise ValueError("JSON 配置必须是对象")
        else:
            self._text_bounds(content)

    def _text_bounds(self, content: str) -> tuple[int, int] | None:
        """生成标记必须完整且位于 frontmatter 之后。"""
        bounds = marker_bounds(content)
        if bounds is not None:
            header, _ = split_frontmatter(content, self.output_filename)
            if bounds[0] < len(header):
                raise ValueError("managed marker 不能位于 frontmatter 内")
        return bounds

    def write(self, project_path: Path, force: bool = False) -> Path:
        """写入文件；force 不能绕过迁移与路径保护。"""
        output = safe_output_path(project_path, self.output_filename)
        legacy_decision(project_path, self.output_filename)
        self.validate_existing(output)
        if output.exists() and not force:
            raise FileExistsError(f"{output} 已存在。使用 --force 覆盖。")
        content = self.generate() if self.is_json else self.generate_marked()
        if output.exists():
            old_content = output.read_bytes().decode("utf-8")
            if not self.is_json:
                marker_bounds(old_content)
                split_frontmatter(old_content, self.output_filename)
        if self.is_json:
            new_data = json.loads(content)
            if not isinstance(new_data, dict):
                raise ValueError("JSON 配置必须是对象")
        output.parent.mkdir(parents=True, exist_ok=True)
        self._write_changed(output, content.encode("utf-8"))
        return output

    def update(self, project_path: Path, force: bool = False) -> Path | None:
        """仅替换合法管理区间或合并 JSON；缺少文件时创建。"""
        output = safe_output_path(project_path, self.output_filename)
        legacy_decision(project_path, self.output_filename)
        if not output.exists():
            return self.write(project_path, force=True)
        return self._update_json(output) if self.is_json else self._update_text(output)

    def _update_text(self, output_path: Path) -> Path | None:
        """保留元数据、BOM、换行和管理区间外的内容。"""
        content = output_path.read_bytes().decode("utf-8")
        bounds = self._text_bounds(content)
        if bounds is None:
            return None
        start, end = bounds
        newline = "\r\n" if "\r\n" in content else "\n"
        managed = self.generate_marked_body().removesuffix("\n").replace("\n", newline)
        self._write_changed(output_path, (content[:start] + managed + content[end:]).encode("utf-8"))
        return output_path

    def _update_json(self, output_path: Path) -> Path:
        """保留已有未知字段和完整服务器定义，不拼接同名服务。"""
        original = output_path.read_bytes()
        old = json.loads(original.decode("utf-8-sig"))
        new = json.loads(self.generate())
        if not isinstance(old, dict) or not isinstance(new, dict):
            raise ValueError(f"JSON 配置必须是对象: {output_path}")
        merged = {**new, **old}
        if isinstance(new.get("mcpServers"), dict) and isinstance(old.get("mcpServers"), dict):
            merged["mcpServers"] = {**new["mcpServers"], **old["mcpServers"]}
        if merged == old:
            return output_path
        newline = "\r\n" if b"\r\n" in original else "\n"
        content = (json.dumps(merged, ensure_ascii=False, indent=2) + "\n").replace("\n", newline)
        if original.startswith(b"\xef\xbb\xbf"):
            content = "\ufeff" + content
        self._write_changed(output_path, content.encode("utf-8"))
        return output_path

    @staticmethod
    def _write_changed(output_path: Path, content: bytes) -> None:
        """相同内容不写盘，以保留 mtime。"""
        if not output_path.exists() or output_path.read_bytes() != content:
            output_path.write_bytes(content)
