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

from ._app_ids import IDS, AppIds
from ._cmd_results import CMD, CachedData, DirContentBtn, ParsedJson
from ._enum_data import OpBtnEnum, OpBtnLabel, SwitchEnum
from ._run_cmd import CommandResult, ReadCmd, ReadVerb
from ._str_enum_names import BindingAction, Tcss
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
from ._utils import Utils

__all__ = [
    "__version__",
    "CMD",
    "IDS",
    "AppIds",
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
    "ParsedJson",
    "ReadCmd",
    "ReadVerb",
    "SectionLabel",
    "SwitchEnum",
    "TabLabel",
    "Tcss",
    "TestPaths",
    "Utils",
]

try:
    __version__ = version("chezmoi-mousse")
except PackageNotFoundError:
    __version__ = "dev"
