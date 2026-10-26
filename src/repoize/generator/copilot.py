"""Copilot 指令生成器"""

from . import get_template_env
from .base import BaseGenerator


class CopilotGenerator(BaseGenerator):
    """生成 .github/copilot-instructions.md 文件。"""

    @property
    def name(self) -> str:
        """生成器名称。"""
        return "copilot-instructions.md"

    @property
    def output_filename(self) -> str:
        """输出文件名。"""
        return ".github/copilot-instructions.md"

    def generate(self) -> str:
        """生成文件内容。"""
        env = get_template_env()
        template = env.get_template("copilot.j2")

        return template.render(**self.template_context())
