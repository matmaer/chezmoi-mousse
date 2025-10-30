from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Literal

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
from chezmoi_mousse._labels import NavBtn, PaneBtn, TabBtn
from chezmoi_mousse._names import AreaName, Canvas, TreeName, ViewName
from chezmoi_mousse._operate_buttons import OperateBtn
from chezmoi_mousse._switches import Switches
from chezmoi_mousse._tcss_classes import Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse._chezmoi import Chezmoi, CommandResults
    from chezmoi_mousse.gui.chezmoi_gui import ChezmoiGUI

type PathDict = dict["Path", str]
type PathList = list["Path"]
type PathType = Literal["file", "dir"]


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
    "Chars",
    "CommandResults",
    "DirTreeNodeData",
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
    "PathDict",
    "PathList",
    "PathType",
    "PreRunData",
    "ReadCmd",
    "ReadVerbs",
    "Switches",
    "TabBtn",
    "Tcss",
    "TreeName",
    "VerbArgs",
    "ViewName",
    "WriteCmd",
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
    path_type: "PathType"


@dataclass(slots=True)
class DirTreeNodeData:
    path: "Path"
    path_type: "PathType"


@dataclass(slots=True)
class OperateLaunchData:
    operate_btn: "OperateBtn"
    node_data: NodeData | DirTreeNodeData


@dataclass(slots=True)
class OperateResultData:
    operate_btn: "OperateBtn | None" = None
    command_results: "CommandResults | None" = None
    operation_executed: bool = False
    path: "Path | None" = None


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
