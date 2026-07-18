# Copyright (C) 2024 matmaer <https://github.com/matmaer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See THIRD_PARTY_LICENSES.md for the chezmoi and textual license information.

from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

from chezmoi_mousse.debug._test_paths import TestPaths
from chezmoi_mousse.enum_data import OpBtnEnum, OpBtnLabel, SwitchEnum
from chezmoi_mousse.run_cmd import CommandResult, ReadCmd, ReadVerb
from chezmoi_mousse.str_enums import (
    Chars,
    FlatBtnLabel,
    LogString,
    OperateString,
    PathKind,
    SectionLabel,
    StatusCode,
    TabLabel,
    Tcss,
)


def save_stacktrace():
    path = Path(tempfile.gettempdir()) / "chezmoi_gui_stacktrace.log"
    if path.exists():
        path.unlink()

    with path.open("a") as f:
        traceback.print_exc(file=f)


__all__ = [
    "save_stacktrace",
    "Chars",
    "CommandResult",
    "FlatBtnLabel",
    "LogString",
    "OpBtnEnum",
    "OpBtnLabel",
    "OperateString",
    "PathKind",
    "ReadCmd",
    "ReadVerb",
    "SectionLabel",
    "StatusCode",
    "SwitchEnum",
    "TabLabel",
    "Tcss",
    "TestPaths",
]
