"""SKILL.md 生成器"""

from . import get_template_env
from .base import BaseGenerator


class SkillMdGenerator(BaseGenerator):
    """生成项目专属 SKILL.md 文件。"""

    @property
    def name(self) -> str:
        """生成器名称。"""
        return "SKILL.md"

    @property
    def output_filename(self) -> str:
        """输出文件名。"""
        return ".claude/skills/project-dev/SKILL.md"

    def generate(self) -> str:
        """生成文件内容。"""
        env = get_template_env()
        template = env.get_template("skill_md.j2")

        return template.render(**self.template_context())
