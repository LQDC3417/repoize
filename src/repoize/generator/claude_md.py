"""CLAUDE.md 生成器"""

from . import get_template_env
from .base import BaseGenerator


class ClaudeMdGenerator(BaseGenerator):
    """生成 CLAUDE.md 文件（Claude Code 专属指令）。"""

    @property
    def name(self) -> str:
        """生成器名称。"""
        return "CLAUDE.md"

    @property
    def output_filename(self) -> str:
        """输出文件名。"""
        return "CLAUDE.md"

    def generate(self) -> str:
        """生成文件内容。"""
        env = get_template_env()
        template = env.get_template("claude_md.j2")

        return template.render(**self.template_context())
