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
    status_files: dict[Path, StatusCode]
    x_files: dict[Path, StatusCode]
    status_dirs_in: dict[Path, StatusCode]
    status_files_in: dict[Path, StatusCode]
    x_dirs_in: list[Path]
    x_files_in: list[Path]

    @property
    def has_status_paths(self) -> bool:
        return True if self.status_files_in or self.status_dirs_in else False

    @property
    def has_x_paths(self) -> bool:
        return True if self.x_files_in or self.x_dirs_in else False


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool
