# Copyright (C) 2024 matmaer <https://github.com/matmaer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See THIRD_PARTY_LICENSES.md for the chezmoi and textual license information.

from importlib.metadata import PackageNotFoundError, version

from ._app_ids import AppIds
from ._app_state import AppState
from ._chezmoi_command import CommandResult, ReadCmd, ReadVerb, WriteCmd
from ._cmd_results import CmdResults
from ._enum_data import OpBtnEnum, SwitchEnum
from ._singletons import CMD, IDS
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
from ._type_hinting import AppType, DirNode, InitCloneData, ParsedJson

__all__ = [
    "__version__",
    "AppIds",
    "AppState",
    "AppType",
    "BindingAction",
    "BindingDescription",
    "Chars",
    "CMD",
    "CmdResults",
    "CommandResult",
    "DirNode",
    "FlatBtnLabel",
    "IDS",
    "InitCloneData",
    "LinkBtn",
    "LogString",
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
