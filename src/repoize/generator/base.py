"""生成器基类"""

import json
import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path

from ..analyzer.project_analyzer import ProjectAnalysis

GENERATED_START = "<!-- repoize:generated-start -->"
GENERATED_END = "<!-- repoize:generated-end -->"
GENERATED_BANNER = "<!-- 本文件由 repoize 自动生成；可修改生成区间之外的内容。 -->"


def _deep_merge(base: dict, override: dict) -> dict:
    """递归深度合并两个字典。override 中的键覆盖 base，嵌套 dict 递归合并。"""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class BaseGenerator(ABC):
    """配置文件生成器基类。"""

    def __init__(self, analysis: ProjectAnalysis):
        """初始化生成器基类。"""
        self.analysis = analysis

    @property
    @abstractmethod
    def name(self) -> str:
        """生成器名称。"""
        ...

    @property
    @abstractmethod
    def output_filename(self) -> str:
        """输出文件名（相对项目根目录）。"""
        ...

    @property
    def is_json(self) -> bool:
        """判断输出是否为 JSON 文件。"""
        return self.output_filename.endswith(".json")

    @abstractmethod
    def generate(self) -> str:
        """生成文件内容。返回 Markdown/JSON 文本。"""
        ...

    def generate_marked(self) -> str:
        """生成带 managed marker 的文本内容。"""
        content = self.generate().strip()
        return f"{GENERATED_START}\n{GENERATED_BANNER}\n{content}\n{GENERATED_END}\n"

    def write(self, project_path: Path, force: bool = False) -> Path:
        """将生成的内容写入文件。返回写入路径。"""
        output_path = project_path / self.output_filename

        if output_path.exists() and not force:
            raise FileExistsError(f"{output_path} 已存在。使用 --force 覆盖。")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.generate() if self.is_json else self.generate_marked()
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def update(self, project_path: Path, force: bool = False) -> Path | None:
        """增量更新文件，尽量保留已有内容。返回写入路径；无法更新时返回 None。"""
        output_path = project_path / self.output_filename
        if not output_path.exists():
            return self.write(project_path, force=True)
        if self.is_json:
            return self._update_json(output_path)
        return self._update_text(output_path)

    def _update_text(self, output_path: Path) -> Path | None:
        """替换 managed marker 区间，保留区间外的手写内容。"""
        old_content = output_path.read_bytes().decode("utf-8")

        if GENERATED_START not in old_content or GENERATED_END not in old_content:
            return None

        prefix, rest = old_content.split(GENERATED_START, 1)
        if GENERATED_END not in rest:
            return None
        suffix = rest.split(GENERATED_END, 1)[1]
        newline = "\r\n" if "\r\n" in rest else "\n"
        # 结束标记后的换行属于手写区间，替换时不重复添加。
        managed = self.generate_marked().removesuffix("\n").replace("\n", newline)
        output_path.write_bytes((prefix + managed + suffix).encode("utf-8"))
        return output_path

    def _update_json(self, output_path: Path) -> Path | None:
        """合并 JSON 对象，保留已有但未生成的键。"""
        old_data = json.loads(output_path.read_text(encoding="utf-8-sig"))
        new_data = json.loads(self.generate())

        if not isinstance(old_data, dict) or not isinstance(new_data, dict):
            raise ValueError(f"JSON 配置必须是对象: {output_path}")

        merged = _deep_merge(new_data, old_data)
        if merged != _deep_merge(old_data, new_data):
            logging.getLogger(__name__).warning("JSON 配置存在冲突，保留已有值: %s", output_path)

        output_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return output_path
