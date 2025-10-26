from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from chezmoi_mousse._chars import Chars
from chezmoi_mousse._chezmoi import (
    CommandResults,
    GlobalCmd,
    LogUtils,
    ManagedPaths,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
    WriteCmd,
)
from chezmoi_mousse._id_classes import CanvasIds, Id
from chezmoi_mousse._labels import NavBtn, OperateBtn, PaneBtn, TabBtn
from chezmoi_mousse._names import AreaName, Canvas, TreeName, ViewName
from chezmoi_mousse._switch_data import Switches
from chezmoi_mousse._tcss_classes import Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse._chezmoi import Chezmoi, CommandResults
    from chezmoi_mousse.gui.chezmoi_gui import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


__all__ = [
    "__version__",
    "AppType",
    "AreaName",
    "Canvas",
    "CanvasIds",
    "WriteCmd",
    "Chars",
    "CommandResults",
    "GlobalCmd",
    "Id",
    "LogUtils",
    "ManagedPaths",
    "NavBtn",
    "NodeData",
    "OperateBtn",
    "OperateLaunchData",
    "OperateResultData",
    "PaneBtn",
    "PreRunData",
    "ReadCmd",
    "ReadVerbs",
    "Switches",
    "TabBtn",
    "Tcss",
    "TreeName",
    "VerbArgs",
    "ViewName",
]


@dataclass(slots=True)
class NodeData:
    found: bool
    path: "Path"
    # chezmoi status codes processed: A, D, M, or a space
    # "node status" codes:
    #   X (no status but managed)
    #   F (fake for the root node)
    status: str
    is_leaf: bool


@dataclass(slots=True)
class OperateLaunchData:
    btn_enum_member: OperateBtn
    button_id: str
    path: "Path"


@dataclass(slots=True)
class OperateResultData:
    path: "Path"
    command_results: "CommandResults | None" = None
    operation_executed: bool = False


@dataclass(slots=True)
class PreRunData:
    chezmoi_instance: "Chezmoi"
    changes_enabled: bool
    chezmoi_found: bool
    dev_mode: bool


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
