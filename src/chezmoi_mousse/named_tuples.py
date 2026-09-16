from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from chezmoi_mousse.str_enums import ReadCmd, WriteCmd

__all__ = [
    "ChezmoiPaths",
    "CmPathChanges",
    "CmPathSets",
    "CommandResult",
    "DumpConfigKeys",
    "InitData",
    "ScanDirItem",
]

ChezmoiPaths = NamedTuple(
    "ChezmoiPaths",
    [
        ("chezmoi_dirs", dict[Path, str]),
        ("chezmoi_files", dict[Path, str]),
        ("managed_dirs", dict[Path, str]),
        ("managed_files", dict[Path, str]),
        ("status_dirs", dict[Path, str]),
        ("status_files", dict[Path, str]),
    ],
)

CmPathChanges = NamedTuple(
    "CmPathChanges",
    [
        ("removed_dirs", list[Path]),
        ("removed_files", list[Path]),
        ("added_files", dict[Path, str]),
        ("added_dirs", dict[Path, str]),
        ("changed_dirs", dict[Path, str]),
        ("changed_files", dict[Path, str]),
        ("top_removed_dirs", list[Path]),
    ],
)


CmPathSets = NamedTuple(
    "CmPathSets",
    [
        # dirty space dirs have nested status paths, clean don't
        ("clean_space_dirs", set[Path]),
        ("dirty_space_dirs", set[Path]),
        # Managed paths, including both files and directories
        ("managed_paths", set[Path]),
        ("status_paths", set[Path]),
        ("missing_paths", set[Path]),
        # Paths in the tree which 'chezmoi add' will do something
        ("add_paths", set[Path]),
        # Paths in the tree which 'chezmoi apply' will do something
        ("apply_paths", set[Path]),
        # Paths in the tree which 'chezmoi re-add' will do something
        ("re_add_paths", set[Path]),
    ],
)


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
