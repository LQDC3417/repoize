"""纯候选变更、脱敏报告与逐文件原子应用。"""

import difflib
import os
import stat
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .targets import legacy_decision, safe_output_path

ACTIONS = ("create", "update", "unchanged", "skip", "conflict", "error")


@dataclass
class FileChange:
    """字节仅供进程内应用；报告只公开固定元数据。"""

    type: str
    path: str
    action: str
    reason: str
    old_bytes: bytes | None = field(default=None, repr=False)
    new_bytes: bytes | None = field(default=None, repr=False)
    field_paths: list[str] = field(default_factory=list)
    comparable: bool = False
    warning: bool = False

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "path": self.path,
            "action": self.action,
            "reason": self.reason,
            "field_paths": self.field_paths,
        }

    def diff(self) -> str:
        """MCP仅显示固定字段类别，文本差异由用户显式请求。"""
        if self.new_bytes is None or self.new_bytes == self.old_bytes:
            return ""
        if self.type == "mcp":
            return "MCP replacement/merge field paths: " + ", ".join(self.field_paths)
        return "".join(
            difflib.unified_diff(
                (self.old_bytes or b"").decode("utf-8").splitlines(keepends=True),
                self.new_bytes.decode("utf-8").splitlines(keepends=True),
                fromfile=self.path,
                tofile=self.path,
            )
        )

    def apply(self, root: Path) -> None:
        """应用同一候选；每次替换前校验路径和原字节，临时文件仅由本次创建。"""

        def revalidate() -> Path:
            output = safe_output_path(root, self.path)
            legacy_decision(root, self.path)
            current = output.read_bytes() if output.exists() else None
            if current != self.old_bytes:
                raise ValueError("concurrent edit detected; refusing replacement")
            return output

        output = revalidate()
        if self.action not in {"create", "update"}:
            return
        if self.new_bytes is None:
            raise ValueError("Missing candidate bytes")
        output.parent.mkdir(parents=True, exist_ok=True)
        output = revalidate()
        mode = stat.S_IMODE(output.stat().st_mode) if self.old_bytes is not None else None
        temp = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=".repoize-", suffix=".tmp", dir=output.parent, delete=False
            ) as file:
                temp = Path(file.name)
                file.write(self.new_bytes)
                file.flush()
                os.fsync(file.fileno())
            if mode is not None:
                os.chmod(temp, mode)
            revalidate()
            os.replace(temp, output)
        finally:
            if temp is not None:
                try:
                    temp.unlink(missing_ok=True)
                except PermissionError:
                    if os.name != "nt":
                        raise
                    # Windows 只读位会阻止删除，仅恢复本次临时文件的可写属性。
                    os.chmod(temp, stat.S_IWRITE)
                    temp.unlink(missing_ok=True)


def change_report(mode: str, changes: list[FileChange]) -> dict:
    """报告不序列化内部字节或用户内容。"""
    return {
        "report_type": "changes",
        "schema_version": 1,
        "mode": mode,
        "changes": [change.to_dict() for change in changes],
        "summary": {action: sum(change.action == action for change in changes) for action in ACTIONS},
    }
