# Copyright (C) 2024 matmaer <https://github.com/matmaer>
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See THIRD_PARTY_LICENSES.md for the chezmoi and textual license information.

from __future__ import annotations

import os
import zlib
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from ._app_ids import IDS, AppIds
from ._cmd_results import CMD, CachedData, DirContentBtn, ParsedJson
from ._enum_data import OpBtnEnum, OpBtnLabel, OpInfoString, SwitchEnum
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

if TYPE_CHECKING:

    from pathlib import Path


class Utils:

    @staticmethod
    def path_to_id(p: Path) -> str:
        b = os.fsencode(os.fspath(p))  # safe, uses fs encoding + surrogateescape
        crc = zlib.crc32(b) & 0xFFFFFFFF  # 0xFFFFFFFF to ensure unsigned 32-bit integer
        return "p_" + str(crc)

    @staticmethod
    def path_to_qid(p: Path) -> str:
        return f"#{Utils.path_to_id(p)}"


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
    "OpInfoString",
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
