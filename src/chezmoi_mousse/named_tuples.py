from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.str_enums import ReadCmd, WriteCmd

__all__ = [
    "CommandResult",
    "DumpConfigKeys",
    "InitData",
    "ScanDirItem",
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


class InitData(NamedTuple):
    which_chezmoi: str | None = None
    which_git: str | None = None
    pilot_mode: bool = False


class ScanDirItem(NamedTuple):
    # matches the argument passed to the os_scan_dir function
    scanned_dir: Path
    # absolute path matchingthe DirEntry.path attribute
    path: Path
    # matches DirEntry attribute
    is_dir: bool
    is_file: bool
    is_symlink: bool
    name: str
    # # if it's a dir or if an exception occurs when calling .stat()
    file_size: int | None
    # set by the os_scan_dir function
    sibling_count: int
    matches_unwanted: bool


from chezmoi_mousse.str_enums import LabelStr

SwitchStates = NamedTuple(
    "SwitchStates",
    [
        (LabelStr.show_unchanged.name, bool),
        (LabelStr.show_unmanaged.name, bool),
        (LabelStr.expand_all.name, bool),
        (LabelStr.show_unwanted.name, bool),
    ],
)
