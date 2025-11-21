from dataclasses import dataclass
from enum import StrEnum, auto
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from ._app_ids import AppIds
from ._button_data import FlatBtn, LinkBtn, OperateBtn, TabBtn
from ._chars import Chars
from ._chezmoi import (
    Chezmoi,
    CommandResult,
    GlobalCmd,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
    WriteCmd,
)
from ._names import (
    ContainerName,
    DataTableName,
    LogName,
    ScreenName,
    TabName,
    TreeName,
    ViewName,
)
from ._switches import Switches
from ._tcss_classes import Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from .gui.textual_app import ChezmoiGUI

type PathDict = "dict[Path, str]"
type PathList = "list[Path]"


class PathType(StrEnum):
    DIR = auto()
    FILE = auto()


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


__all__ = [
    "__version__",
    "AppIds",
    "AppType",
    "Chars",
    "Chezmoi",
    "CommandResult",
    "ContainerName",
    "DataTableName",
    "DirTreeNodeData",
    "FlatBtn",
    "GlobalCmd",
    "LinkBtn",
    "LogName",
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
    "ScreenName",
    "SplashData",
    "Switches",
    "TabBtn",
    "TabName",
    "Tcss",
    "TreeName",
    "VerbArgs",
    "ViewName",
    "WriteCmd",
]


class ScreenIds:
    def __init__(self) -> None:
        # Construct the ids for each screen
        self.init = AppIds(ScreenName.init)
        self.install_help = AppIds(ScreenName.install_help)
        self.splash = AppIds(ScreenName.splash)
        self.main = AppIds(ScreenName.main)
        self.operate = AppIds(ScreenName.operate)


class TabIds:
    def __init__(self) -> None:
        # Construct the ids for the tabs
        self.add = AppIds(TabName.add)
        self.apply = AppIds(TabName.apply)
        self.config = AppIds(TabName.config)
        self.help = AppIds(TabName.help)
        self.logs = AppIds(TabName.logs)
        self.re_add = AppIds(TabName.re_add)


@dataclass(slots=True)
class DirTreeNodeData:
    path: "Path"
    path_type: "PathType"


@dataclass(slots=True)
class NodeData:
    found: "bool"
    path: "Path"
    # Chezmoi status codes processed: A, D, M, or a space
    # Additional "node status" codes: X (no status but managed)
    status: "str"
    path_type: "PathType"


@dataclass(slots=True)
class OperateScreenData:
    node_data: "NodeData | DirTreeNodeData"
    operate_btn: "OperateBtn"
    command_result: "CommandResult | None" = None
    operation_executed: "bool" = False
    path: "Path | None" = None


@dataclass(slots=True)
class ParsedConfig:
    dest_dir: "Path"
    git_autoadd: "bool"
    source_dir: "Path"
    git_autocommit: "bool"
    git_autopush: "bool"


@dataclass(slots=True, frozen=True)
class PreRunData:
    chezmoi_found: "bool"
    dev_mode: "bool"
    force_init_screen: "bool"
    screen_id: ScreenIds = ScreenIds()
    pane_id: TabIds = TabIds()


@dataclass(slots=True)
class SplashData:
    cat_config: "CommandResult"
    doctor: "CommandResult"
    executed_commands: "list[CommandResult]"
    git_log: "CommandResult"
    ignored: "CommandResult"
    parsed_config: "ParsedConfig"
    template_data: "CommandResult"
    verify: "CommandResult"
    # init field not needed if chezmoi is already initialized
    init: "CommandResult | None" = None


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
