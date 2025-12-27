"""This package does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

Only launcher.py imports from textual, ChezmoiGUI which inherits from the
textual App class.
"""

from importlib.metadata import PackageNotFoundError, version

from ._app_ids import IDS, AppIds
from ._chezmoi_command import (
    ChezmoiCommand,
    CommandResult,
    GlobalCmd,
    ReadCmd,
    ReadVerbs,
    VerbArgs,
    WriteCmd,
)
from ._chezmoi_paths import ChezmoiPaths, PathDict, PathList
from ._operate_button_data import OpBtnEnum, OpBtnLabels
from ._str_enum_bindings import BindingAction, BindingDescription
from ._str_enum_names import LogName, PathKind, ScreenName, TabName, TreeName
from ._str_enum_tcss import Tcss
from ._str_enums import (
    Chars,
    DestDirStrings,
    FlatBtn,
    LinkBtn,
    LogStrings,
    OperateStrings,
    SectionLabels,
    TabBtn,
)
from ._switch_data import Switches
from ._type_checking import (
    AppType,
    DiffData,
    InitCloneData,
    NodeData,
    ParsedConfig,
    SplashData,
)

__all__ = [
    "__version__",
    # Id related
    "IDS",
    "AppIds",
    # Operations
    "InitCloneData",
    "OpBtnLabels",
    "OpBtnEnum",
    "OperateStrings",
    # _chezmoi.py
    "ChezmoiCommand",
    "CommandResult",
    "GlobalCmd",
    "PathDict",
    "PathList",
    "ReadCmd",
    "ReadVerbs",
    "WriteCmd",
    "VerbArgs",
    # _chezmoi_paths.py
    "ChezmoiPaths",
    # Other
    "AppType",
    "BindingAction",
    "BindingDescription",
    "Chars",
    "DiffData",
    "DestDirStrings",
    "FlatBtn",
    "LinkBtn",
    "LogName",
    "LogStrings",
    "NodeData",
    "ParsedConfig",
    "PathKind",
    "ScreenName",
    "SectionLabels",
    "SplashData",
    "Switches",
    "TabBtn",
    "TabName",
    "Tcss",
    "TreeName",
]


try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
