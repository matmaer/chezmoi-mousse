from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from chezmoi_mousse._chars import Chars
from chezmoi_mousse._chezmoi import (
    ChangeCmd,
    GlobalCmd,
    ManagedPaths,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
)
from chezmoi_mousse._id_classes import CanvasIds, Id
from chezmoi_mousse._labels import (
    NavBtn,
    OperateBtn,
    PaneBtn,
    SubTitles,
    TabBtn,
)
from chezmoi_mousse._names import (
    ActiveCanvas,
    AreaName,
    Canvas,
    TreeName,
    ViewName,
)
from chezmoi_mousse._switch_data import Switches
from chezmoi_mousse._tcss_classes import Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse._chezmoi import Chezmoi
    from chezmoi_mousse.gui.chezmoi_gui import ChezmoiGUI


class AppType:
    """Type hint for self.app attributes in widgets and screens."""

    if TYPE_CHECKING:
        app: "ChezmoiGUI"


__all__ = [
    "__version__",
    "ActiveCanvas",
    "AppType",
    "AreaName",
    "Canvas",
    "CanvasIds",
    "ChangeCmd",
    "Chars",
    "GlobalCmd",
    "Id",
    "LogUtils",
    "ManagedPaths",
    "NavBtn",
    "NodeData",
    "OperateBtn",
    "OperateData",
    "PaneBtn",
    "PreRunData",
    "ReadCmd",
    "ReadVerbs",
    "SubTitles",
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
class OperateData:
    button_id: str
    path: "Path"


@dataclass(slots=True)
class PreRunData:
    chezmoi_instance: "Chezmoi"
    changes_enabled: bool
    chezmoi_found: bool
    dev_mode: bool


class LogUtils:
    @staticmethod
    def pretty_cmd_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return "chezmoi " + " ".join(
            [
                _
                for _ in command[1:]
                if _
                not in GlobalCmd.default_args.value
                + filter_git_log_args
                + [
                    VerbArgs.format_json.value,
                    VerbArgs.path_style_absolute.value,
                ]
            ]
        )


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
