from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Literal

from chezmoi_mousse._chars import Chars
from chezmoi_mousse._chezmoi import (
    Chezmoi,
    CommandResult,
    GlobalCmd,
    LogUtils,
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
    "Chezmoi",
    "CommandResult",
    "DirTreeNodeData",
    "GlobalCmd",
    "Id",
    "LogUtils",
    "NavBtn",
    "NodeData",
    "OperateBtn",
    "OperateScreenData",
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
class OperateScreenData:
    node_data: "NodeData | DirTreeNodeData"
    operate_btn: "OperateBtn"
    command_result: "CommandResult | None" = None
    operation_executed: bool = False
    path: "Path | None" = None


@dataclass(slots=True, frozen=True)
class PreRunData:
    changes_enabled: bool
    chezmoi_found: bool
    dev_mode: bool


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
