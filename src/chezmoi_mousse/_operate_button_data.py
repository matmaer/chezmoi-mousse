"""This module does not import anything from textual, it only contains classes imported
at module init before launching the textual app, and attributes accessed after the app
is launched."""

from dataclasses import dataclass
from enum import Enum

from ._chezmoi_command import WriteCmd
from ._str_enums import OpBtnLabels, OperateStrings

__all__ = ["OpBtnEnum"]


@dataclass(slots=True)
class OpBtnData:
    label: str
    pretty_cmd: str
    write_cmd: WriteCmd
    info_strings: list[str] | None = None
    info_sub_title: str | None = None
    info_title: str | None = None


class OpBtnEnum(Enum):
    add = OpBtnData(
        label=OpBtnLabels.add_review,
        pretty_cmd=WriteCmd.add.pretty_cmd,
        write_cmd=WriteCmd.add,
        info_strings=[OperateStrings.add_path_info],
        info_sub_title=OperateStrings.add_subtitle,
        info_title=OpBtnLabels.add_run,
    )
    apply = OpBtnData(
        label=OpBtnLabels.apply_review,
        pretty_cmd=WriteCmd.apply.pretty_cmd,
        write_cmd=WriteCmd.apply,
        info_strings=[OperateStrings.apply_path_info],
        info_sub_title=OperateStrings.apply_subtitle,
        info_title=OpBtnLabels.apply_run,
    )
    destroy = OpBtnData(
        label=OpBtnLabels.destroy_review,
        pretty_cmd=WriteCmd.destroy.pretty_cmd,
        write_cmd=WriteCmd.destroy,
        info_strings=[OperateStrings.destroy_path_info],
        info_sub_title=OperateStrings.destroy_subtitle,
        info_title=OpBtnLabels.destroy_run,
    )
    forget = OpBtnData(
        label=OpBtnLabels.forget_review,
        pretty_cmd=WriteCmd.forget.pretty_cmd,
        write_cmd=WriteCmd.forget,
        info_strings=[OperateStrings.forget_path_info],
        info_sub_title=OperateStrings.forget_subtitle,
        info_title=OpBtnLabels.forget_run,
    )
    re_add = OpBtnData(
        label=OpBtnLabels.re_add_review,
        pretty_cmd=WriteCmd.re_add.pretty_cmd,
        write_cmd=WriteCmd.re_add,
        info_strings=[OperateStrings.re_add_path_info],
        info_sub_title=OperateStrings.re_add_subtitle,
        info_title=OpBtnLabels.re_add_run,
    )
    init = OpBtnData(
        label=OpBtnLabels.init_review,
        pretty_cmd=WriteCmd.init_new.pretty_cmd,
        write_cmd=WriteCmd.init_new,
        info_strings=[OperateStrings.init_new_info],
        info_sub_title=OperateStrings.init_subtitle,
        info_title=OpBtnLabels.init_run,
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def pretty_cmd(self) -> str:
        return self.value.pretty_cmd

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
