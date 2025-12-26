"""This package does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

Only launcher.py imports from textual, ChezmoiGUI which inherits from the
textual App class.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from ._app_ids import IDS, AppIds
from ._chezmoi_command import (
    ChezmoiCommand,
    CommandResult,
    GlobalCmd,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
    WriteCmd,
)
from ._chezmoi_paths import ChezmoiPaths, PathDict, PathList
from ._operate_button_data import OpBtnLabels, OperateBtn
from ._str_enum_bindings import BindingAction, BindingDescription
from ._str_enum_names import LogName, PathKind, ScreenName, TabName, TreeName
from ._str_enum_tcss import Tcss
from ._str_enums import (
    Chars,
    DestDirStrings,
    FlatBtn,
    LinkBtn,
    LogStrings,
    OperateStrings,
    SectionLabels,
    TabBtn,
)
from ._switch_data import Switches

if TYPE_CHECKING:
    from pathlib import Path

    from textual.widgets import Static

    from .gui.textual_app import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: ChezmoiGUI


__all__ = [
    "__version__",
    # Id related
    "IDS",
    "AppIds",
    # Operations
    "InitCloneData",
    "OpBtnLabels",
    "OperateBtn",
    "OperateStrings",
    # _chezmoi.py
    "ChezmoiCommand",
    "CommandResult",
    "GlobalCmd",
    "PathDict",
    "PathList",
    "ReadCmd",
    "ReadVerbs",
    "WriteCmd",
    "VerbArgs",
    # _chezmoi_paths.py
    "ChezmoiPaths",
    # Other
    "AppType",
    "BindingAction",
    "BindingDescription",
    "Chars",
    "DestDirStrings",
    "FlatBtn",
    "LinkBtn",
    "LogName",
    "LogStrings",
    "NodeData",
    "ParsedConfig",
    "PathKind",
    "ScreenName",
    "SectionLabels",
    "SplashData",
    "Switches",
    "TabBtn",
    "TabName",
    "Tcss",
    "TreeName",
]


@dataclass(slots=True)
class DiffData:
    diff_cmd_label: str
    diff_lines: list[Static]


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
    git_autoadd: bool
    source_dir: Path
    git_autocommit: bool
    git_autopush: bool


@dataclass(slots=True)
class SplashData:
    cat_config: CommandResult
    doctor: CommandResult
    git_log: CommandResult
    ignored: CommandResult
    parsed_config: ParsedConfig
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


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
