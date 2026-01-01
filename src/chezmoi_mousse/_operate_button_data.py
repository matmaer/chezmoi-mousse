"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OpButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

from ._chezmoi_command import WriteCmd
from ._str_enums import OperateStrings

__all__ = ["OpBtnLabels", "OpBtnEnum"]


class OpBtnLabels(StrEnum):
    add_run = "Run Chezmoi Add"
    add_review = "Review Add Path"
    apply_review = "Review Apply Path"
    apply_run = "Run Chezmoi Apply"
    cancel = "Cancel"
    destroy_run = "Run Chezmoi Destroy"
    destroy_review = "Review Destroy Path"
    exit_app = "Exit App"
    forget_run = "Run Chezmoi Forget"
    forget_review = "Review Forget Path"
    init_run = "Run Chezmoi Init"
    init_review = "Review Init Chezmoi"
    re_add_review = "Review Re-Add Path"
    re_add_run = "Run Chezmoi Re-Add"
    reload = "Reload"


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd
    info_strings: list[str] | None = None
    info_sub_title: str | None = None
    info_title: str | None = None


class OpBtnEnum(Enum):
    add = OpBtnData(
        label=OpBtnLabels.add_review,
        write_cmd=WriteCmd.add,
        info_strings=[OperateStrings.add_path_info],
        info_sub_title=OperateStrings.add_subtitle,
        info_title=OpBtnLabels.add_run,
    )
    apply = OpBtnData(
        label=OpBtnLabels.apply_review,
        write_cmd=WriteCmd.apply,
        info_strings=[OperateStrings.apply_path_info],
        info_sub_title=OperateStrings.apply_subtitle,
        info_title=OpBtnLabels.apply_run,
    )
    destroy = OpBtnData(
        label=OpBtnLabels.destroy_review,
        write_cmd=WriteCmd.destroy,
        info_strings=[OperateStrings.destroy_path_info],
        info_sub_title=OperateStrings.destroy_subtitle,
        info_title=OpBtnLabels.destroy_run,
    )
    forget = OpBtnData(
        label=OpBtnLabels.forget_review,
        write_cmd=WriteCmd.forget,
        info_strings=[OperateStrings.forget_path_info],
        info_sub_title=OperateStrings.forget_subtitle,
        info_title=OpBtnLabels.forget_run,
    )
    re_add = OpBtnData(
        label=OpBtnLabels.re_add_review,
        write_cmd=WriteCmd.re_add,
        info_strings=[OperateStrings.re_add_path_info],
        info_sub_title=OperateStrings.re_add_subtitle,
        info_title=OpBtnLabels.re_add_run,
    )
    init = OpBtnData(
        label=OpBtnLabels.init_review, write_cmd=WriteCmd.init_new
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def write_cmd(self) -> WriteCmd:
        return self.value.write_cmd

    @property
    def full_cmd(self) -> list[str]:
        return self.write_cmd.subprocess_arguments

    @property
    def info_strings(self) -> str:
        if self.value.info_strings is None:
            return ""
        return "\n".join(self.value.info_strings)

    @property
    def info_sub_title(self) -> str | None:
        return self.value.info_sub_title

    @property
    def info_title(self) -> str | None:
        return self.value.info_title
