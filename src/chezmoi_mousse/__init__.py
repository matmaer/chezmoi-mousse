# Copyright (C) 2024 matmaer <https://github.com/matmaer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See THIRD_PARTY_LICENSES.md for the chezmoi and textual license information.

from __future__ import annotations

from typing import TYPE_CHECKING

from ._app_ids import AppIds, CanvasIds
from ._cmd_results import CMD, CachedData
from ._enum_data import OpBtnEnum, OpBtnLabel, SwitchEnum
from ._run_cmd import CommandResult, ReadCmd, ReadVerb
from ._str_enums import (
    Chars,
    FlatBtnLabel,
    LogString,
    OperateString,
    SectionLabel,
    StatusCode,
    TabLabel,
    Tcss,
)
from .debug._test_paths import TestPaths

if TYPE_CHECKING:
    from .textual_app import ChezmoiGUI

__all__ = [
    "CMD",
    "AppIds",
    "CanvasIds",
    "CachedData",
    "Chars",
    "ChezmoiGUI",
    "CommandResult",
    "FlatBtnLabel",
    "LogString",
    "OpBtnEnum",
    "OpBtnLabel",
    "OperateString",
    "ReadCmd",
    "ReadVerb",
    "SectionLabel",
    "StatusCode",
    "SwitchEnum",
    "TabLabel",
    "Tcss",
    "TestPaths",
]
