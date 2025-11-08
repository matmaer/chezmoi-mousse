from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Literal

from chezmoi_mousse._button_data import FlatBtn, LinkBtn, OperateBtn, TabBtn
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
from chezmoi_mousse._names import CanvasName, ContainerName, TreeName, ViewName
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
    "CanvasName",
    "Chars",
    "Chezmoi",
    "CommandResult",
    "CommandsData",
    "ContainerName",
    "DirTreeNodeData",
    "FlatBtn",
    "GlobalCmd",
    "LinkBtn",
    "LogUtils",
    "NodeData",
    "OperateBtn",
    "OperateScreenData",
    "ParsedConfig",
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
class ParsedConfig:
    dest_dir: "Path"
    git_autoadd: bool
    source_dir: "Path"
    git_autocommit: bool
    git_autopush: bool


@dataclass(slots=True)
class CommandsData:
    cat_config: "CommandResult"
    doctor: "CommandResult"
    executed_commands: "list[CommandResult]"
    ignored: "CommandResult"
    parsed_config: ParsedConfig
    template_data: "CommandResult"


@dataclass(slots=True)
class NodeData:
    found: bool
    path: "Path"
    # Chezmoi status codes processed: A, D, M, or a space
    # Additional "node status" codes: X (no status but managed)
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
    chezmoi_found: bool
    dev_mode: bool


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
