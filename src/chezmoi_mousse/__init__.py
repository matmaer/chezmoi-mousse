from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from chezmoi_mousse._chezmoi_cmd import (
    ChangeCmd,
    Chezmoi,
    GlobalCmd,
    ManagedStatusData,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
)
from chezmoi_mousse._id_classes import Id, ScreenIds, Switches, TabIds
from chezmoi_mousse._str_enums import (
    Area,
    Chars,
    LogName,
    NavBtn,
    OperateBtn,
    OperateHelp,
    PaneBtn,
    ScreenName,
    TabBtn,
    Tcss,
    TreeName,
    ViewName,
)

__all__ = [
    # from this file
    "__version__",
    "ParsedJson",
    "PathDict",
    # from _chezmoi_cmd.py
    "ChangeCmd",
    "Chezmoi",
    "GlobalCmd",
    "ManagedStatusData",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
    # from _id_classes.py
    "Id",
    "ScreenIds",
    "Switches",
    "TabIds",
    # from _str_enums.py
    "Area",
    "Chars",
    "LogName",
    "NavBtn",
    "OperateBtn",
    "OperateHelp",
    "ScreenName",
    "TabBtn",
    "PaneBtn",
    "Tcss",
    "TreeName",
    "ViewName",
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]
