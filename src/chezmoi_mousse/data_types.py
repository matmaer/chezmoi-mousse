from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import (
    LabelStr,
    LogStr,
    ReadCmd,
    StatusCode,
    TreeName,
    WriteCmd,
)

if TYPE_CHECKING:
    from typing import Any

    from chezmoi_mousse.str_enums import StatusCode


__all__ = [
    "CommandResult",
    "DirData",
    "InitData",
    "IterDirResult",
    "NodeData",
    "ParsedDumpConfig",
]


@dataclass(slots=True, frozen=True, kw_only=True)
class CommandResult:
    cmd_enum: WriteCmd | ReadCmd
    full_cmd: str
    interactive_approved: bool | None = None
    _verb_arg: str | list[str] | None
    returncode: int | None
    std_err: str
    std_out: str
    time_stamp: str

    @property
    def out_list(self) -> list[str]:
        return self.std_out.splitlines()

    @property
    def dry_run(self) -> bool:
        return self.cmd_enum in WriteCmd.dry_commands()

    @property
    def _pretty_verb_arg(self) -> str:
        if self._verb_arg is None:
            pretty_arg = ""
        elif isinstance(self._verb_arg, list) and self.cmd_enum is ReadCmd.source_path:
            if len(self._verb_arg) > 0:
                pretty_arg = (
                    LogStr.on_managed_dirs
                    if Path(self._verb_arg[0]).is_dir()
                    else LogStr.on_managed_files
                )
            else:
                pretty_arg = ""
        elif self._verb_arg != "" and isinstance(self._verb_arg, str):
            pretty_arg = path_funcs.get_rel_path_str(self._verb_arg)
        else:
            pretty_arg = ""
        return pretty_arg

    @property
    def pretty_cmd(self) -> str:
        return (f"{self.cmd_enum.pretty_cmd} {self._pretty_verb_arg}").rstrip()


@dataclass(frozen=True)
class ParsedDumpConfig:
    dump_config_std_out: str

    @cached_property
    def _parsed_cfg(self) -> dict[str, Any]:
        return json.loads(self.dump_config_std_out)

    @property
    def auto_add(self) -> bool:
        return self._parsed_cfg["git"]["autoadd"]

    @property
    def auto_commit(self) -> bool:
        return self._parsed_cfg["git"]["autocommit"]

    @property
    def auto_push(self) -> bool:
        return self._parsed_cfg["git"]["autopush"]

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self._parsed_cfg["destDir"])

    @property
    def dest_dir_str(self) -> str:
        return self._parsed_cfg["destDir"]

    @property
    def source_dir_str(self) -> str:
        return self._parsed_cfg["sourceDir"]

    @cached_property
    def git_index(self) -> Path:
        return Path(self._parsed_cfg["sourceDir"]) / ".git" / "index"


@dataclass(slots=True, frozen=True)
class InitData:
    pilot_mode: bool


@dataclass(slots=True, frozen=True)
class IterDirResult:
    error: str
    dirs: dict[Path, NodeData]
    files: dict[Path, NodeData]


@dataclass(slots=True, frozen=True)
class DirData:
    nested_managed: bool
    nested_status: bool
    nested_un_managed: bool
    nested_filtered: bool
    dest_dir: bool

    @classmethod
    def for_file(cls) -> DirData:
        return cls(
            nested_managed=False,
            nested_status=False,
            nested_un_managed=False,
            nested_filtered=False,
            dest_dir=False,
        )


@dataclass(slots=True)
class NodeData:
    dir_path: bool
    exists: bool
    managed: bool
    path: Path
    source_path: Path | None
    status: StatusCode | None
    filtered: bool | None
    dir_data: DirData = field(default_factory=DirData.for_file)

    @property
    def source_path_str(self) -> str:
        return str(self.source_path) if self.source_path is not None else ""

    @property
    def file_path(self) -> bool:
        return not self.dir_path

    @property
    def status_path(self) -> bool:
        return self.status is not None

    @property
    def _filtered_dir(self) -> bool:
        return self.dir_path and self.filtered is True

    @property
    def _filtered_file(self) -> bool:
        return self.file_path and self.filtered is True

    @property
    def _filtered_path(self) -> bool:
        return self._filtered_dir or self._filtered_file

    def get_main_label(self, label_size: int) -> str:
        if self.dir_data.dest_dir:
            label_str = LabelStr.dest_dir
        elif self.dir_path:
            label_str = LabelStr.managed_dir if self.managed else LabelStr.un_man_dir
        else:
            label_str = LabelStr.managed_file if self.managed else LabelStr.un_man_file

        full_label = f"{label_str} {self.path}"
        if len(full_label) <= label_size or self.dir_data.dest_dir:
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
        managed_dir = self.dir_path and self.managed
        status_dir = managed_dir and self.status_path
        include_dir_for_sp_tree = status_dir or self.dir_data.nested_status

        managed_file = self.file_path and self.managed
        status_file = managed_file and self.status_path
        include_sp = status_file or include_dir_for_sp_tree

        if tree_name in (TreeName.managed_sp):
            return include_sp
        elif tree_name in (TreeName.managed_amp):
            return self.managed
        elif tree_name in (TreeName.filtered_unman_sp):
            return include_sp or self.dir_data.nested_filtered or self._filtered_path
        elif tree_name in (TreeName.filtered_unman_amp):
            return self.managed or self.dir_data.nested_filtered or self._filtered_path
        else:
            return True
