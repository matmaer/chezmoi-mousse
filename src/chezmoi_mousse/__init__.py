from importlib.metadata import PackageNotFoundError, version

from chezmoi_mousse._chezmoi_cmd import (
    ChangeCmd,
    GlobalCmd,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
)
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
    "__version__",
    "ParsedJson",
    "PathDict",
    # from _chezmoi_cmd.py
    "ChangeCmd",
    "GlobalCmd",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
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

from pathlib import Path
from typing import Any

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]
