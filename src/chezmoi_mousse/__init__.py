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
from ._chezmoi_paths import ChezmoiPath, PathDict
from ._operate_button_data import OpBtnEnum
from ._str_enum_bindings import BindingAction, BindingDescription
from ._str_enum_names import PathKind, ScreenName, TabName, Tcss, TreeName
from ._str_enums import (
    Chars,
    FlatBtnLabel,
    LinkBtn,
    LogString,
    OpBtnLabel,
    OperateString,
    SectionLabel,
    StatusCode,
    TabBtn,
)
from ._switch_data import SwitchEnum
from ._type_checking import AppType, CmdResults, InitCloneData, NodeData, ParsedConfig

__all__ = [
    "__version__",
    "AppIds",
    "AppState",
    "AppType",
    "BindingAction",
    "BindingDescription",
    "Chars",
    "ChezmoiCommand",
    "ChezmoiPath",
    "CmdResults",
    "CommandResult",
    "FlatBtnLabel",
    "GlobalCmd",
    "IDS",
    "InitCloneData",
    "LinkBtn",
    "LogString",
    "NodeData",
    "OpBtnEnum",
    "OpBtnLabel",
    "OperateString",
    "ParsedConfig",
    "PathDict",
    "PathKind",
    "ReadCmd",
    "ReadVerb",
    "ScreenName",
    "SectionLabel",
    "StatusCode",
    "SwitchEnum",
    "TabBtn",
    "TabName",
    "Tcss",
    "TreeName",
    "VerbArgs",
    "WriteCmd",
    # ._str_enums
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
