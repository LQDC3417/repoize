"""MCP Server 配置生成器"""

import json

from ..targets import MCP_TARGET
from .base import BaseGenerator


class McpConfigGenerator(BaseGenerator):
    """生成 MCP Server 配置文件。"""

    @property
    def name(self) -> str:
        """生成器名称。"""
        return "MCP 配置"

    @property
    def output_filename(self) -> str:
        """输出文件名。"""
        return MCP_TARGET

    def generate(self) -> str:
        """生成文件内容。"""
        return json.dumps({"mcpServers": {}}, ensure_ascii=False, indent=2) + "\n"
