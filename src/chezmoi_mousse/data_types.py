from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.str_enums import BtnLabel, TreeName

if TYPE_CHECKING:
    from chezmoi_mousse.str_enums import ReadCmd, StatusCode, WriteCmd

__all__ = [
    "CommandResult",
    "DumpConfigKeys",
    "InitData",
    "IterDirResult",
    "NodeData",
    "OperateViewData",
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


@dataclass(slots=True, frozen=True)
class InitData:
    pilot_mode: bool = False
    which_chezmoi: str | None = None
    which_git: str | None = None


@dataclass(slots=True, frozen=True)
class IterDirResult:
    # status codes will be either Sc.UU (unmanaged) or None (unwanted)
    error: str
    exceptions: dict[Path, str]
    symlinks: list[Path]
    dirs: dict[Path, NodeData]
    files: dict[Path, NodeData]


@dataclass(slots=True, frozen=True)
class NodeData:
    dir_path: bool
    exists: bool
    has_nested_managed: bool
    has_nested_status: bool
    main_label: str
    managed: bool
    path: Path
    source_path: Path | None
    status: StatusCode | None
    un_wanted_dir: bool
    un_wanted_file: bool
    has_nested_unmanaged: bool = False
    dest_dir: bool = False

    @property
    def has_status(self) -> bool:
        return self.status is not None

    @property
    def enable_op_btn_map(self) -> dict[BtnLabel, bool]:
        # basic button enable/disable rules, affected paths could still determine no-op
        has_diff = bool(self.status) or self.has_nested_status
        enable_add_btn = not self.dest_dir and (
            not self.managed or has_diff or self.has_nested_unmanaged
        )
        enable_destroy_btn = (
            self.managed
            and self.exists
            and not self.dest_dir
            and (not self.dir_path or not self.has_nested_unmanaged)
        )
        return {
            BtnLabel.chezmoi_add: enable_add_btn,
            BtnLabel.chezmoi_forget: self.managed and not self.dest_dir,
            BtnLabel.chezmoi_destroy: enable_destroy_btn,
            BtnLabel.chezmoi_apply: has_diff,
            BtnLabel.chezmoi_re_add: self.exists and has_diff,
        }

    def include_in_tree(self, tree_name: TreeName) -> bool:
        show_in_all = self.status is not None or self.has_nested_status
        un_wanted = self.un_wanted_dir or self.un_wanted_file
        if tree_name in (TreeName.managed_only_sp, TreeName.managed_only_sp_xpd):
            return show_in_all
        elif tree_name in (TreeName.managed_all_mp, TreeName.managed_all_mp_xpd):
            return self.managed
        elif tree_name in (TreeName.un_man_plus_sp, TreeName.un_man_plus_sp_xpd):
            return not un_wanted or show_in_all
        elif tree_name in (TreeName.un_man_plus_amp, TreeName.un_man_plus_amp_xpd):
            return not un_wanted or self.managed
        elif tree_name in (
            TreeName.un_wanted_plus_sp,
            TreeName.un_wanted_plus_sp_xpd,
        ):
            return not self.managed or show_in_all
        else:
            return True


@dataclass(slots=True)
class OperateViewData:
    last_displayed_path: Path | None = None
    displayed_paths: set[Path] = field(default_factory=set[Path])
    no_show_paths: set[Path] = field(default_factory=set[Path])

    @property
    def known_paths(self) -> set[Path]:
        return self.displayed_paths | self.no_show_paths


@dataclass(slots=True, frozen=True)
class StreamEvent:
    data: list[str]
    is_prompt: bool
