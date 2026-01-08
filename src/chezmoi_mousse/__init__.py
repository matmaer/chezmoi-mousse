# Copyright (C) 2024 matmaer <https://github.com/matmaer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See THIRD_PARTY_LICENSES.md for the chezmoi and textual license information.

from importlib.metadata import PackageNotFoundError, version

from ._app_ids import IDS, AppIds
from ._app_state import AppState
from ._chezmoi_command import (
    ChezmoiCommand,
    CommandResult,
    GlobalCmd,
    ReadCmd,
    ReadVerb,
    VerbArgs,
    WriteCmd,
)
from ._chezmoi_paths import ChezmoiPaths, PathDict
from ._operate_button_data import OpBtnEnum, OpBtnLabels
from ._str_enum_bindings import BindingAction, BindingDescription
from ._str_enum_names import PathKind, ScreenName, TabName, Tcss, TreeName
from ._str_enums import (
    Chars,
    FlatBtn,
    LinkBtn,
    LogStrings,
    OperateStrings,
    SectionLabels,
    StatusCode,
    TabBtn,
)
from ._switch_data import Switches
from ._type_checking import (
    AppType,
    CmdResults,
    InitCloneData,
    NodeData,
    ParsedConfig,
)

__all__ = [
    "__version__",
    # ._app_state
    "AppState",
    # ._app_ids
    "IDS",
    "AppIds",
    # ._chezmoi_command
    "ChezmoiCommand",
    "CommandResult",
    "GlobalCmd",
    "ReadCmd",
    "ReadVerb",
    "VerbArgs",
    "WriteCmd",
    # ._chezmoi_paths
    "ChezmoiPaths",
    "PathDict",
    # ._operate_button_data
    "OpBtnEnum",
    "OpBtnLabels",
    # ._str_enum_bindings
    "BindingAction",
    "BindingDescription",
    # ._str_enum_names
    "PathKind",
    "ScreenName",
    "StatusCode",
    "TabName",
    "Tcss",
    "TreeName",
    # ._str_enums
    "Chars",
    "FlatBtn",
    "LinkBtn",
    "LogStrings",
    "OperateStrings",
    "SectionLabels",
    "TabBtn",
    # ._switch_data
    "Switches",
    # ._type_checking
    "AppType",
    "CmdResults",
    "InitCloneData",
    "NodeData",
    "ParsedConfig",
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
