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
    ScreenName,
    TabBtn,
    TabName,
    Tcss,
    TreeName,
    ViewName,
)

__all__ = [
    "__version__",
    "NodeData",
    "ParsedJson",
    "PathDict",
    "SplashReturnData",
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
    "TabName",
    "Tcss",
    "TreeName",
    "ViewName",
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"


from dataclasses import dataclass
from pathlib import Path
from typing import Any

type ParsedJson = dict[str, Any]
type PathDict = dict[Path, str]


@dataclass
class NodeData:
    found: bool
    path: Path
    status: str
    is_dir: bool


@dataclass
class SplashReturnData:
    doctor: str
    dir_status_lines: str
    file_status_lines: str
    managed_dirs: str
    managed_files: str
