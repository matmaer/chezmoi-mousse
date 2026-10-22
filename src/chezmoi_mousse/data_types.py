from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.str_enums import LabelStr, TreeName

if TYPE_CHECKING:
    from typing import Any

    from chezmoi_mousse.str_enums import ReadCmd, StatusCode, WriteCmd

__all__ = [
    "CommandResult",
    "InitData",
    "IterDirResult",
    "NodeData",
    "ParsedDumpConfig",
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


@dataclass(frozen=True)
class ParsedDumpConfig:
    _dump_config_std_out: str

    @cached_property
    def parsed_cfg(self) -> dict[str, Any]:
        return json.loads(self._dump_config_std_out)

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self.parsed_cfg["destDir"])

    @property
    def git_index(self) -> Path:
        return Path(self.parsed_cfg["sourceDir"]) / ".git" / "index"

    @property
    def auto_add(self) -> bool:
        return self.parsed_cfg["git"]["autoadd"]

    @property
    def auto_commit(self) -> bool:
        return self.parsed_cfg["git"]["autocommit"]

    @property
    def auto_push(self) -> bool:
        return self.parsed_cfg["git"]["autopush"]


@dataclass(slots=True, frozen=True)
class InitData:
    pilot_mode: bool = False
    _which_chezmoi: str | None = None
    _which_git: str | None = None

    @property
    def which_chezmoi(self) -> str:
        if self._which_chezmoi is None:
            raise RuntimeError(
                "Trying to run a chezmoi command when it's not available or before ",
                "it's set in InitData",
            )

        elif self._which_git is None:
            raise RuntimeError(
                "Trying to run a chezmoi command when git is not available or before "
                "it's set in InitData"
            )
        return self._which_chezmoi


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
    def _wanted_dir(self) -> bool:
        return self.dir_path and self.wanted is True

    @property
    def _wanted_file(self) -> bool:
        return self.file_path and self.wanted is True

    @property
    def _wanted_path(self) -> bool:
        return self._wanted_dir or self._wanted_file

    def get_main_label(self, label_size: int) -> str:
        if self.dest_dir:
            label_str = LabelStr.dest_dir
        elif self.dir_path:
            label_str = LabelStr.managed_dir if self.managed else LabelStr.un_man_dir
        else:
            label_str = LabelStr.managed_file if self.managed else LabelStr.un_man_file

        full_label = f"{label_str} {self.path}"
        if len(full_label) <= label_size or self.dest_dir:
            return full_label

        max_path_length = label_size - len(label_str) - 5  # space, 3 dots plus os sep

        count = 0
        current_len = 0

        for part in reversed(self.path.parts):
            part_len = len(part) + 1
            if current_len + part_len > max_path_length:
                break
            current_len += part_len
            count += 1

        if count == 0:  # Fallback to full last component if even 1 part doesn't fit
            return f"{label_str} ...{os.sep}{self.path.name}"

        return f"{label_str} ...{os.sep}{Path(*self.path.parts[-count:])}"

    def include_in_tree(self, tree_name: TreeName) -> bool:
        include_dir_for_sp_tree = self.status_dir or self.nested_status
        include_sp = self.status_file or include_dir_for_sp_tree

        if tree_name in (TreeName.managed_sp, TreeName.managed_sp_xpd):
            return include_sp
        elif tree_name in (TreeName.managed_amp, TreeName.managed_amp_xpd):
            return self.managed
        elif tree_name in (TreeName.wanted_plus_sp, TreeName.wanted_plus_sp_xpd):
            return include_sp or self.nested_wanted or self._wanted_path
        elif tree_name in (TreeName.wanted_plus_amp, TreeName.wanted_plus_amp_xpd):
            return self.managed or self.nested_wanted or self._wanted_path
        elif tree_name in (TreeName.un_wanted_plus_sp, TreeName.un_wanted_plus_sp_xpd):
            return include_sp or self.nested_un_managed or self.un_managed
        else:
            return True


@dataclass(slots=True, frozen=True)
class StreamEvent:
    data: list[str]
    is_prompt: bool
    # for prompts: the question preceding the options, e.g. "Apply .foo"
    prompt_question: str = ""
    # only set on the final event of a process
    returncode: int | None = None
    std_out: str = ""
    std_err: str = ""
