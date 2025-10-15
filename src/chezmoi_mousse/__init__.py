from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from chezmoi_mousse._chars import Chars
from chezmoi_mousse._chezmoi import (
    ChangeCmd,
    GlobalCmd,
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
    from chezmoi_mousse._chezmoi import Chezmoi
    from chezmoi_mousse.gui.app import ChezmoiGUI


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
    "NavBtn",
    "OperateBtn",
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
class PreRunData:
    chezmoi_instance: "Chezmoi"
    changes_enabled: bool
    chezmoi_found: bool
    dev_mode: bool


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
