from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.str_enums import ReadCmd, StatusCode, WriteCmd

__all__ = [
    "CommandResult",
    "DumpConfigKeys",
    "InitData",
    "IterDirResult",
    "NodeData",
]


class CommandResult(NamedTuple):
    cmd_enum: WriteCmd | ReadCmd | None
    full_cmd: str
    out_txt: str
    path_arg: Path | None
    pretty_cmd: str
    returncode: int | None
    std_err: str
    std_out: str
    out_list: list[str]
    time_stamp: str


class DumpConfigKeys(NamedTuple):
    dest_dir_path: Path | None = None
    auto_add_bool: bool | None = None
    auto_commit_bool: bool | None = None
    auto_push_bool: bool | None = None

    @property
    def dest_dir(self) -> Path:
        if self.dest_dir_path is None:
            raise RuntimeError("Accessing dest_dir before the config is parsed")
        return self.dest_dir_path

    @property
    def auto_add(self) -> bool:
        if self.auto_add_bool is None:
            raise RuntimeError("Accessing auto_add before the config is parsed")
        return self.auto_add_bool

    @property
    def auto_commit(self) -> bool:
        if self.auto_commit_bool is None:
            raise RuntimeError("Accessing auto_commit before the config is parsed")
        return self.auto_commit_bool

    @property
    def auto_push(self) -> bool:
        if self.auto_push_bool is None:
            raise RuntimeError("Accessing auto_push before the config is parsed")
        return self.auto_push_bool

    @property
    def git_config_dict(self) -> dict[str, bool]:
        return {
            "auto_add": self.auto_add,
            "auto_commit": self.auto_commit,
            "auto_push": self.auto_push,
        }


class InitData(NamedTuple):
    pilot_mode: bool = False
    which_chezmoi: str | None = None
    which_git: str | None = None


class IterDirResult(NamedTuple):
    # status codes will be either Sc.UU (unmanaged) or None (unwanted)
    error: str
    exceptions: dict[Path, str]
    symlinks: list[Path]
    dirs: dict[Path, NodeData]
    files: dict[Path, NodeData]


@dataclass(slots=True)
class NodeData:
    dir_path: bool
    exists: bool
    file_path: bool
    has_nested_status: bool
    has_nested_un_managed: bool | None
    has_un_wanted_dir_parent: bool
    main_label: str
    managed_dir: bool
    managed_file: bool
    path: Path
    status_dir: bool
    status_file: bool
    status: StatusCode | None
    un_wanted_dir: bool
    un_wanted_file: bool
    dest_dir: bool = False
