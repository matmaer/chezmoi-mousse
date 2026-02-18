from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ._chezmoi_command import WriteCmd
from ._str_enums import StatusCode

if TYPE_CHECKING:
    from typing import Any

    from .gui.textual_app import ChezmoiGUI

__all__ = ["AppType", "DirNode", "InitCloneData", "ParsedJson"]


type ParsedJson = dict[str, Any]


class AppType:
    app: ChezmoiGUI


@dataclass(slots=True)
class DirNode:
    dir_status: StatusCode
    status_dirs_in: dict[Path, StatusCode]
    status_files_in: dict[Path, StatusCode]
    x_dirs_in: dict[Path, StatusCode]
    x_files_in: dict[Path, StatusCode]
    dirs_in_for_tree: dict[Path, StatusCode]


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool
