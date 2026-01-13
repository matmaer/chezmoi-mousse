from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._chezmoi_command import CommandResult, WriteCmd
    from ._chezmoi_paths import PathKind, StatusCode
    from .gui.textual_app import ChezmoiGUI


type Value = str | dict[str, "Value"]  # recursive type alias

__all__ = [
    "AppType",
    "CmdResults",
    "InitCloneData",
    "NodeData",
    "ParsedConfig",
    "PathNode",
]


class AppType:
    app: ChezmoiGUI


@dataclass(slots=True)
class CmdResults:
    cat_config: CommandResult | None = None
    doctor: CommandResult | None = None
    dump_config: CommandResult | None = None
    git_log: CommandResult | None = None
    ignored: CommandResult | None = None
    managed_dirs: CommandResult | None = None
    managed_files: CommandResult | None = None
    status_dirs: CommandResult | None = None
    status_files: CommandResult | None = None
    template_data: CommandResult | None = None
    verify: CommandResult | None = None
    install_help_data: dict[str, Value] | None = None

    @property
    def executed_commands(self) -> list[CommandResult]:
        # Return the field value which are CommandResult and not None
        return [
            getattr(self, field.name)
            for field in fields(self)
            if getattr(self, field.name) is not None
        ]


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool


@dataclass(slots=True)
class NodeData:
    found: bool
    path: Path
    status: StatusCode
    path_kind: PathKind


@dataclass(slots=True)
class ParsedConfig:
    dest_dir: Path
    git_auto_add: bool
    git_auto_commit: bool
    git_auto_push: bool
    source_dir: Path


@dataclass(slots=True)
class PathNode:
    found: bool
    path: Path
    # Chezmoi status codes processed: A, D, M, or a space
    # Additional "node status" codes: X (no status but managed)
    path_kind: PathKind
    status_pair: tuple[StatusCode, StatusCode]
