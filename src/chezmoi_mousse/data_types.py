from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import BtnLabel, LabelStr, TreeName

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
    wanted: bool
    dest_dir: bool = False

    @property
    def file_path(self) -> bool:
        return not self.dir_path

    @property
    def has_status(self) -> bool:
        return self.status is not None

    @property
    def un_managed(self) -> bool:
        return not self.managed

    @property
    def enable_op_btn_map(self) -> dict[BtnLabel, bool]:
        # basic button enable/disable rules, affected paths could still determine no-op
        has_diff = self.status is not None or self.nested_status
        enable_add_btn = not self.dest_dir and (
            self.un_managed or has_diff or self.nested_wanted
        )
        enable_destroy_btn = self.managed and self.exists and not self.nested_un_managed
        return {
            BtnLabel.chezmoi_add: enable_add_btn,
            BtnLabel.chezmoi_forget: self.managed and not self.dest_dir,
            BtnLabel.chezmoi_destroy: enable_destroy_btn,
            BtnLabel.chezmoi_apply: has_diff,
            BtnLabel.chezmoi_re_add: self.exists and has_diff,
        }

    @property
    def main_label(self) -> str:
        if self.dest_dir:
            label_str = LabelStr.dest_dir
        elif self.dir_path:
            label_str = LabelStr.managed_dir if self.managed else LabelStr.un_man_dir
        else:
            label_str = LabelStr.managed_file if self.managed else LabelStr.un_man_file

        path_str = " " + path_funcs.get_rel_path_str(self.path)

        if len(label_str) + len(path_str) > 70:
            available = 70 - len(label_str)
            path_str = f"{path_str[: available - 3]}..."

        return label_str + path_str

    def include_in_tree(self, tree_name: TreeName) -> bool:
        managed_dir = self.dir_path and self.managed
        managed_file = self.file_path and self.managed

        status_dir = managed_dir and (self.has_status or self.nested_status)
        status_file = managed_file and self.has_status
        status_path = status_file or status_dir

        un_managed_dir = self.dir_path and self.un_managed
        un_managed_file = self.file_path and self.un_managed
        un_managed_path = un_managed_dir or un_managed_file

        wanted_dir = self.dir_path and self.wanted
        wanted_file = self.file_path and self.wanted
        wanted_path = wanted_dir or wanted_file

        man_dir_with_wanted = managed_dir and self.nested_wanted
        man_dir_with_un_managed = managed_dir and self.nested_un_managed

        if tree_name in (TreeName.managed_sp, TreeName.managed_sp_xpd):
            return status_path
        elif tree_name in (TreeName.managed_amp, TreeName.managed_amp_xpd):
            return self.managed
        elif tree_name in (TreeName.wanted_plus_sp, TreeName.wanted_plus_sp_xpd):
            return status_path or man_dir_with_wanted or wanted_path
        elif tree_name in (TreeName.wanted_plus_amp, TreeName.wanted_plus_amp_xpd):
            return self.managed or man_dir_with_wanted or wanted_path
        elif tree_name in (TreeName.un_wanted_plus_sp, TreeName.un_wanted_plus_sp_xpd):
            return status_path or man_dir_with_un_managed or un_managed_path
        else:
            return True


@dataclass(slots=True, frozen=True)
class StreamEvent:
    data: list[str]
    is_prompt: bool
