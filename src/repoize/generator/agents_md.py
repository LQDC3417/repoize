"""AGENTS.md 生成器"""

from . import get_template_env
from .base import BaseGenerator


class AgentsMdGenerator(BaseGenerator):
    """生成 AGENTS.md 文件。"""

    @property
    def name(self) -> str:
        """生成器名称。"""
        return "AGENTS.md"

    @property
    def output_filename(self) -> str:
        """输出文件名。"""
        return "AGENTS.md"

    def generate(self) -> str:
        """生成文件内容。"""
        env = get_template_env()
        template = env.get_template("agents_md.j2")

        return template.render(**self.template_context())
