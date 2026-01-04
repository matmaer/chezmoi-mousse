from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING

from ._chezmoi_command import CommandResult, WriteCmd
from ._str_enum_names import PathKind

if TYPE_CHECKING:
    from textual.widgets import Static
    from textual.widgets.tree import TreeNode

    from .gui.textual_app import ChezmoiGUI


__all__ = [
    "AppType",
    "DiffData",
    "ExpandedNodeData",
    "InitCloneData",
    "NodeData",
    "ParsedConfig",
    "SplashData",
]


class AppType:
    app: ChezmoiGUI


@dataclass(slots=True)
class DiffData:
    diff_cmd_label: str
    diff_lines: list[Static]


@dataclass(slots=True)
class ExpandedNodeData:
    apply_expanded: list[TreeNode[NodeData]]
    re_add_expanded: list[TreeNode[NodeData]]


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool


@dataclass(slots=True)
class NodeData:
    found: bool
    path: Path
    # Chezmoi status codes processed: A, D, M, or a space
    # Additional "node status" codes: X (no status but managed)
    status: str
    path_kind: PathKind


@dataclass(slots=True)
class ParsedConfig:
    dest_dir: Path
    git_auto_add: bool
    git_auto_commit: bool
    git_auto_push: bool
    source_dir: Path


@dataclass(slots=True)
class SplashData:
    cat_config: CommandResult
    doctor: CommandResult
    git_log: CommandResult
    ignored: CommandResult
    template_data: CommandResult
    verify: CommandResult

    @property
    def executed_commands(self) -> list[CommandResult]:
        # Return the field value which are CommandResult and not None
        return [
            getattr(self, field.name)
            for field in fields(self)
            if isinstance(getattr(self, field.name), CommandResult)
        ]
