# Copyright (C) 2024 matmaer <https://github.com/matmaer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See THIRD_PARTY_LICENSES.md for the chezmoi and textual license information.

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from ._app_ids import IDS, AppIds
from ._cmd_results import CMD, CachedData, DirContentBtn, ParsedJson
from ._enum_data import OpBtnEnum, OpBtnLabel, OpInfoString, SwitchEnum
from ._run_cmd import CommandResult, ReadCmd, ReadVerb
from ._str_enum_names import BindingAction, ScreenName, Tcss
from ._str_enums import (
    BindingDescription,
    Chars,
    FlatBtnLabel,
    LinkBtn,
    LogString,
    OperateString,
    SectionLabel,
    TabLabel,
)
from ._test_paths import TestPaths

if TYPE_CHECKING:

    from .gui.textual_app import ChezmoiGUI


class AppType:
    app: ChezmoiGUI


__all__ = [
    "__version__",
    "CMD",
    "IDS",
    "AppIds",
    "AppType",
    "BindingAction",
    "BindingDescription",
    "CachedData",
    "DirContentBtn",
    "Chars",
    "CommandResult",
    "FlatBtnLabel",
    "LinkBtn",
    "LogString",
    "OpBtnEnum",
    "OpBtnLabel",
    "OperateString",
    "OpInfoString",
    "ParsedJson",
    "ReadCmd",
    "ReadVerb",
    "ScreenName",
    "SectionLabel",
    "SwitchEnum",
    "TabLabel",
    "Tcss",
    "TestPaths",
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
