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
    exists: bool
    main_label: str
    managed_dir: bool
    managed_file: bool
    path: Path
    status_dir: bool
    status_file: bool
    status: StatusCode | None
    un_man_dir: bool
    un_man_file: bool
    un_wanted_dir: bool
    un_wanted_file: bool
    has_nested_unmanaged: bool | None
    dest_dir: bool = False
    has_nested_managed_dirs: bool = False
    has_nested_managed: bool = False
    has_nested_status: bool = False

    @property
    def has_status(self) -> bool:
        return self.status_dir or self.status_file

    @property
    def known_file(self) -> bool:
        return self.managed_file or self.un_man_file

    @property
    def known_dir(self) -> bool:
        return self.managed_dir or self.un_man_dir or self.dest_dir

    @property
    def managed(self) -> bool:
        return self.managed_dir or self.managed_file

    @property
    def managed_edge_dir(self) -> bool:
        return self.managed_dir and not self.has_nested_managed_dirs

    @property
    def un_managed(self) -> bool:
        return self.un_man_dir or self.un_man_file

    @property
    def un_wanted(self) -> bool:
        return self.un_wanted_dir or self.un_wanted_file
