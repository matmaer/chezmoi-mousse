from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from chezmoi_mousse.cm_command import WriteCmd
from chezmoi_mousse.str_enums import OpBtnLabel, OpInfoString, SwitchLabel

__all__ = ["OpBtnEnum", "SwitchEnum"]


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd | None = None
    op_info_string: str | None = None
    op_info_title: str | None = None
    op_info_subtitle: str | None = None
    path_arg: "Path | None" = None


class OpBtnEnum(Enum):

    cancel = OpBtnData(label=OpBtnLabel.cancel)
    create_diffs = OpBtnData(label=OpBtnLabel.create_diffs)
    create_paths = OpBtnData(label=OpBtnLabel.create_paths)
    list_test_paths = OpBtnData(label=OpBtnLabel.list_test_paths)
    log_memory = OpBtnData(label=OpBtnLabel.log_memory)
    refresh_tree = OpBtnData(label=OpBtnLabel.refresh_tree)
    reload = OpBtnData(label=OpBtnLabel.reload)
    remove_paths = OpBtnData(label=OpBtnLabel.remove_paths)

    add_review = OpBtnData(
        label=OpBtnLabel.add_review,
        write_cmd=WriteCmd.add,
        op_info_string=OpInfoString.add_path_info,
        op_info_subtitle=OpInfoString.add_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    add_run = OpBtnData(
        label=OpBtnLabel.add_run,
        write_cmd=WriteCmd.add,
        op_info_string=OpInfoString.add_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    apply_review = OpBtnData(
        label=OpBtnLabel.apply_review,
        write_cmd=WriteCmd.apply,
        op_info_string=OpInfoString.apply_path_info,
        op_info_subtitle=OpInfoString.apply_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    apply_run = OpBtnData(
        label=OpBtnLabel.apply_run,
        write_cmd=WriteCmd.apply,
        op_info_string=OpInfoString.apply_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    destroy_review = OpBtnData(
        label=OpBtnLabel.destroy_review,
        write_cmd=WriteCmd.destroy,
        op_info_string=OpInfoString.destroy_path_info,
        op_info_subtitle=OpInfoString.destroy_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    destroy_run = OpBtnData(
        label=OpBtnLabel.destroy_run,
        write_cmd=WriteCmd.destroy,
        op_info_string=OpInfoString.destroy_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    forget_review = OpBtnData(
        label=OpBtnLabel.forget_review,
        write_cmd=WriteCmd.forget,
        op_info_string=OpInfoString.forget_path_info,
        op_info_subtitle=OpInfoString.forget_subtitle,
        op_info_title=OpInfoString.ready_to_run,
        path_arg=None,
    )
    forget_run = OpBtnData(
        label=OpBtnLabel.forget_run,
        write_cmd=WriteCmd.forget,
        op_info_string=OpInfoString.forget_path_info,
        op_info_title=OpInfoString.run_completed,
    )
    re_add_review = OpBtnData(
        label=OpBtnLabel.re_add_review,
        write_cmd=WriteCmd.re_add,
        op_info_string=OpInfoString.re_add_path_info,
        op_info_subtitle=OpInfoString.re_add_subtitle,
        op_info_title=OpInfoString.ready_to_run,
    )
    re_add_run = OpBtnData(
        label=OpBtnLabel.re_add_run,
        write_cmd=WriteCmd.re_add,
        op_info_string=OpInfoString.re_add_path_info,
        op_info_title=OpInfoString.run_completed,
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def write_cmd(self) -> WriteCmd:
        if self.value.write_cmd is None:
            raise ValueError(f"OpBtnEnum member {self.name} has no write_cmd")
        return self.value.write_cmd

    @property
    def op_info_string(self) -> str:
        if self.value.op_info_string is None:
            raise ValueError(f"OpBtnEnum member {self.name} has no op_info_string")
        return self.value.op_info_string

    @property
    def op_info_subtitle(self) -> str | None:
        return self.value.op_info_subtitle

    @property
    def op_info_title(self) -> str | None:
        return self.value.op_info_title

    @property
    def path_arg(self) -> "Path | None":
        return self.value.path_arg

    @path_arg.setter
    def path_arg(self, value: "Path | None") -> None:
        self.value.path_arg = value

    @classmethod
    def review_to_run(cls, btn_label: OpBtnLabel) -> "OpBtnEnum":
        _mapping = {
            OpBtnLabel.add_review: cls.add_run,
            OpBtnLabel.apply_review: cls.apply_run,
            OpBtnLabel.destroy_review: cls.destroy_run,
            OpBtnLabel.forget_review: cls.forget_run,
            OpBtnLabel.re_add_review: cls.re_add_run,
        }
        return _mapping[btn_label]

    @classmethod
    def review_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls.add_review,
            cls.apply_review,
            cls.destroy_review,
            cls.forget_review,
            cls.re_add_review,
        }

    @classmethod
    def run_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls.add_run,
            cls.apply_run,
            cls.destroy_run,
            cls.forget_run,
            cls.re_add_run,
        }


class SwitchData(NamedTuple):
    label: str
    enabled_tooltip: str


class SwitchEnum(Enum):

    # Apply and Re-Add tab
    show_unchanged = SwitchData(
        label=SwitchLabel.show_unchanged,
        enabled_tooltip=(
            "Include unchanged paths, which are not found in the 'chezmoi status' "
            "output."
        ),
    )
    show_unmanaged_files = SwitchData(
        label=SwitchLabel.show_unmanaged_files,
        enabled_tooltip=("If enabled, also show unmanaged files."),
    )
    expand_all = SwitchData(
        label=SwitchLabel.expand_all, enabled_tooltip=("Expand all directories.")
    )

    # Add Tab
    hide_unmanaged_dirs = SwitchData(
        label=SwitchLabel.hide_unmanaged_dirs,
        enabled_tooltip=("If enabled, hide unmanaged directories."),
    )
    show_managed = SwitchData(
        label=SwitchLabel.show_managed,
        enabled_tooltip=("If enabled, also show already managed paths."),
    )
    show_unwanted = SwitchData(
        label=SwitchLabel.show_unwanted,
        enabled_tooltip=(
            "Include files and directories considered as 'unwanted' for a dotfile "
            "manager. These include cache, temporary, trash (recycle bin) and other "
            "similar files or directories."
        ),
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip
