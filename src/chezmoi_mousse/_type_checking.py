from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._chezmoi_command import WriteCmd
from ._str_enums import StatusCode

__all__ = ["InitCloneData"]


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


@dataclass(slots=True)
class InitCloneData:
    init_cmd: WriteCmd
    init_arg: str
    valid_arg: bool
