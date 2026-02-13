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
from ._chezmoi_command import CMD, CommandResult, ReadCmd, ReadVerb, WriteCmd
from ._cmd_results import CmdResults
from ._enum_data import OpBtnEnum, SwitchEnum
from ._str_enum_names import BindingAction, ScreenName, TabName, Tcss, TreeName
from ._str_enums import (
    BindingDescription,
    Chars,
    FlatBtnLabel,
    LinkBtn,
    LogString,
    OpBtnLabel,
    OperateString,
    SectionLabel,
    StatusCode,
    SubTabLabel,
)
from ._type_checking import AppType, InitCloneData, NodeData, ParsedJson

__all__ = [
    "__version__",
    "CMD",
    "AppIds",
    "AppState",
    "AppType",
    "BindingAction",
    "BindingDescription",
    "Chars",
    "CmdResults",
    "CommandResult",
    "FlatBtnLabel",
    "IDS",
    "InitCloneData",
    "LinkBtn",
    "LogString",
    "NodeData",
    "OpBtnEnum",
    "OpBtnLabel",
    "OperateString",
    "ParsedJson",
    "ReadCmd",
    "ReadVerb",
    "ScreenName",
    "SectionLabel",
    "StatusCode",
    "SubTabLabel",
    "SwitchEnum",
    "TabName",
    "Tcss",
    "TreeName",
    "WriteCmd",
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
