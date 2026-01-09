"""This module does not import anything from textual, it only contains classes imported
at module init before launching the textual app, and attributes accessed after the app
is launched."""

from dataclasses import dataclass
from enum import Enum

from ._chezmoi_command import WriteCmd
from ._str_enums import OpBtnLabel, OperateString

__all__ = ["OpBtnEnum"]


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd
    info_strings: list[str] | None = None
    info_sub_title: str | None = None
    info_title: str | None = None


class OpBtnEnum(Enum):
    add = OpBtnData(
        label=OpBtnLabel.add_review,
        write_cmd=WriteCmd.add,
        info_strings=[OperateString.add_path_info],
        info_sub_title=OperateString.add_subtitle,
        info_title=OpBtnLabel.add_run,
    )
    apply = OpBtnData(
        label=OpBtnLabel.apply_review,
        write_cmd=WriteCmd.apply,
        info_strings=[OperateString.apply_path_info],
        info_sub_title=OperateString.apply_subtitle,
        info_title=OpBtnLabel.apply_run,
    )
    destroy = OpBtnData(
        label=OpBtnLabel.destroy_review,
        write_cmd=WriteCmd.destroy,
        info_strings=[OperateString.destroy_path_info],
        info_sub_title=OperateString.destroy_subtitle,
        info_title=OpBtnLabel.destroy_run,
    )
    forget = OpBtnData(
        label=OpBtnLabel.forget_review,
        write_cmd=WriteCmd.forget,
        info_strings=[OperateString.forget_path_info],
        info_sub_title=OperateString.forget_subtitle,
        info_title=OpBtnLabel.forget_run,
    )
    re_add = OpBtnData(
        label=OpBtnLabel.re_add_review,
        write_cmd=WriteCmd.re_add,
        info_strings=[OperateString.re_add_path_info],
        info_sub_title=OperateString.re_add_subtitle,
        info_title=OpBtnLabel.re_add_run,
    )
    init = OpBtnData(
        label=OpBtnLabel.init_review,
        write_cmd=WriteCmd.init_new,
        info_strings=[OperateString.init_new_info],
        info_sub_title=OperateString.init_subtitle,
        info_title=OpBtnLabel.init_run,
    )

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def pretty_cmd(self) -> str:
        return self.write_cmd.pretty_cmd

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
