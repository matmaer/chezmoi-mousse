from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from ._app_ids import AppIds
from ._button_data import FlatBtn, LinkBtn, OperateBtn, TabBtn
from ._chezmoi import (
    Chezmoi,
    CommandResult,
    GlobalCmd,
    PathDict,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
    WriteCmd,
)
from ._str_enums import (
    BindingDescription,
    Chars,
    ContainerName,
    DataTableName,
    HeaderTitle,
    LogName,
    PathKind,
    ScreenName,
    TabName,
    Tcss,
    TreeName,
    ViewName,
)
from ._switch_data import Switches

if TYPE_CHECKING:
    from pathlib import Path

    from .gui.textual_app import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


__all__ = [
    "__version__",
    "AppIds",
    "AppType",
    "BindingDescription",
    "Chars",
    "Chezmoi",
    "CommandResult",
    "ContainerName",
    "DataTableName",
    "DirTreeNodeData",
    "FlatBtn",
    "GlobalCmd",
    "HeaderTitle",
    "LinkBtn",
    "LogName",
    "NodeData",
    "OperateBtn",
    "OperateScreenData",
    "ParsedConfig",
    "PathDict",
    "PathKind",
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


@dataclass(slots=True)
class DirTreeNodeData:
    path: "Path"
    path_type: "PathKind"


@dataclass(slots=True)
class NodeData:
    found: "bool"
    path: "Path"
    # Chezmoi status codes processed: A, D, M, or a space
    # Additional "node status" codes: X (no status but managed)
    status: "str"
    path_type: "PathKind"


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
