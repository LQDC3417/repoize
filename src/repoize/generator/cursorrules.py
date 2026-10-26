"""Cursor .mdc 生成器"""

from ..targets import CURSOR_TARGET
from . import get_template_env
from .base import BaseGenerator


class CursorRulesGenerator(BaseGenerator):
    """生成 Cursor .mdc 文件。"""

    @property
    def name(self) -> str:
        """生成器名称。"""
        return ".cursorrules"

    @property
    def output_filename(self) -> str:
        """输出文件名。"""
        return CURSOR_TARGET

    def generate(self) -> str:
        """生成文件内容。"""
        env = get_template_env()
        template = env.get_template("cursorrules.j2")

        return template.render(**self.template_context())
