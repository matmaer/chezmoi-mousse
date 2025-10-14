from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from chezmoi_mousse._chars import Chars
from chezmoi_mousse._chezmoi_cmd import (
    ChangeCmd,
    GlobalCmd,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
)
from chezmoi_mousse._id_classes import CanvasIds, Id
from chezmoi_mousse._labels import NavBtn, OperateBtn, PaneBtn, TabBtn
from chezmoi_mousse._names import (
    ActiveCanvas,
    AreaName,
    Canvas,
    TreeName,
    ViewName,
)
from chezmoi_mousse._subtitles import SubTitles
from chezmoi_mousse._switch_data import Switches
from chezmoi_mousse._tcss_classes import Tcss

__all__ = [
    "__version__",
    "Any",
    "ActiveCanvas",
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
    "ParsedJson",
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

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]
