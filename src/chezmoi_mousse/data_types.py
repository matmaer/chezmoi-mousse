from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import LabelStr, TreeName

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.str_enums import ReadCmd, StatusCode, WriteCmd

__all__ = [
    "CommandResult",
    "DumpConfigKeys",
    "InitData",
    "IterDirResult",
    "NodeData",
    "StreamEvent",
]


@dataclass(slots=True, frozen=True)
class CommandResult:
    cmd_enum: WriteCmd | ReadCmd | None
    full_cmd: str
    pretty_cmd: str
    returncode: int | None
    std_err: str
    std_out: str
    out_list: list[str]
    time_stamp: str


@dataclass(slots=True, frozen=True)
class DumpConfigKeys:
    dest_dir_path: Path | None = None
    _auto_add_bool: bool | None = None
    _auto_commit_bool: bool | None = None
    _auto_push_bool: bool | None = None

    @property
    def dest_dir(self) -> Path:
        if self.dest_dir_path is None:
            raise RuntimeError("Accessing dest_dir before the config is parsed")
        return self.dest_dir_path

    @property
    def auto_add(self) -> bool:
        if self._auto_add_bool is None:
            raise RuntimeError("Accessing auto_add before the config is parsed")
        return self._auto_add_bool

    @property
    def auto_commit(self) -> bool:
        if self._auto_commit_bool is None:
            raise RuntimeError("Accessing auto_commit before the config is parsed")
        return self._auto_commit_bool

    @property
    def auto_push(self) -> bool:
        if self._auto_push_bool is None:
            raise RuntimeError("Accessing auto_push before the config is parsed")
        return self._auto_push_bool

    @property
    def git_config_dict(self) -> dict[str, bool]:
        return {
            "auto_add": self.auto_add,
            "auto_commit": self.auto_commit,
            "auto_push": self.auto_push,
        }


@dataclass(slots=True, frozen=True)
class InitData:
    pilot_mode: bool = False
    which_chezmoi: str | None = None
    which_git: str | None = None


@dataclass(slots=True, frozen=True)
class IterDirResult:
    error: str
    dirs: dict[Path, NodeData]
    files: dict[Path, NodeData]


@dataclass(slots=True, frozen=True)
class NodeData:
    dir_path: bool
    exists: bool
    managed: bool
    nested_managed: bool
    nested_status: bool
    nested_un_managed: bool
    nested_wanted: bool
    path: Path
    source_path: Path | None
    status: StatusCode | None
    wanted: bool | None
    dest_dir: bool = False

    @property
    def rel_path(self) -> str:
        return path_funcs.get_rel_path_str(self.path)

    @property
    def rel_source_path(self) -> str:
        if self.source_path is None:
            return self.rel_path
        return path_funcs.get_rel_path_str(self.source_path)

    @property
    def file_path(self) -> bool:
        return not self.dir_path

    @property
    def has_status(self) -> bool:
        return self.status is not None

    @property
    def managed_dir(self) -> bool:
        return self.dir_path and self.managed

    @property
    def managed_file(self) -> bool:
        return self.file_path and self.managed

    @property
    def status_dir(self) -> bool:
        return self.managed_dir and self.has_status

    @property
    def status_file(self) -> bool:
        return self.managed_file and self.has_status

    @property
    def un_managed(self) -> bool:
        return not self.managed

    @property
    def un_managed_dir(self) -> bool:
        return self.dir_path and self.un_managed

    @property
    def un_managed_file(self) -> bool:
        return self.file_path and self.un_managed

    @property
    def wanted_dir(self) -> bool:
        return self.dir_path and self.wanted is not None and self.wanted is True

    @property
    def wanted_file(self) -> bool:
        return self.file_path and self.wanted is not None and self.wanted is True

    @property
    def wanted_path(self) -> bool:
        return self.wanted_dir or self.wanted_file

    @property
    def main_label(self) -> str:
        if self.dest_dir:
            label_str = LabelStr.dest_dir
        elif self.dir_path:
            label_str = LabelStr.managed_dir if self.managed else LabelStr.un_man_dir
        else:
            label_str = LabelStr.managed_file if self.managed else LabelStr.un_man_file

        full_label = f"{label_str} {self.path}"
        if len(full_label) <= 70:
            return full_label

        max_path_length = 70 - len(label_str) - 5  # space, 3 dots plus os sep

        # Count how many parts fit from the right
        count = 0
        current_len = 0

        for part in reversed(self.path.parts):
            part_len = len(part) + 1
            if current_len + part_len > max_path_length:
                if count == 0:
                    return f"{label_str} {self.path.name}"
                break
            current_len += part_len
            count += 1

        # self.path.parents[count - 1] is the directory where the loop stopped
        trimmed_path = self.path.relative_to(self.path.parents[count - 1])

        return f"{label_str} ...{os.sep}{trimmed_path}"

    def include_in_tree(self, tree_name: TreeName) -> bool:
        include_dir_for_sp_tree = self.status_dir or self.nested_status
        include_sp = self.status_file or include_dir_for_sp_tree

        if tree_name in (TreeName.managed_sp, TreeName.managed_sp_xpd):
            return include_sp
        elif tree_name in (TreeName.managed_amp, TreeName.managed_amp_xpd):
            return self.managed
        elif tree_name in (TreeName.wanted_plus_sp, TreeName.wanted_plus_sp_xpd):
            return include_sp or self.nested_wanted or self.wanted_path
        elif tree_name in (TreeName.wanted_plus_amp, TreeName.wanted_plus_amp_xpd):
            return self.managed or self.nested_wanted or self.wanted_path
        elif tree_name in (TreeName.un_wanted_plus_sp, TreeName.un_wanted_plus_sp_xpd):
            return include_sp or self.nested_un_managed or self.un_managed
        else:
            return True


@dataclass(slots=True, frozen=True)
class StreamEvent:
    data: list[str]
    is_prompt: bool
