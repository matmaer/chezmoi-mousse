"""This module does not import anything from textual, it only contains classes imported
at module init before launching the textual app, and attributes accessed after the app
is launched."""

from dataclasses import dataclass
from enum import Enum

from ._chezmoi_command import WriteCmd
from ._str_enums import OpBtnLabel, OperateString, SwitchLabel

__all__ = ["OpBtnEnum", "SwitchEnum"]


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
    def write_cmd(self) -> WriteCmd:
        return self.value.write_cmd

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


@dataclass(frozen=True, slots=True)
class SwitchData:
    label: str
    enabled_tooltip: str
    disabled_tooltip: str | None


class SwitchEnum(Enum):

    init_repo_switch = SwitchData(
        label=SwitchLabel.init_repo,
        enabled_tooltip="Initialize a new chezmoi repository, or clone an existing remote chezmoi repository.",
        disabled_tooltip=None,
    )
    expand_all = SwitchData(
        label=SwitchLabel.expand_all,
        enabled_tooltip='Expand all managed directories. Showing unchanged depending on the "show unchanged files" switch.',
        disabled_tooltip="Switch to Tree to enable this switch.",
    )
    unchanged = SwitchData(
        label=SwitchLabel.unchanged,
        enabled_tooltip="Include files unchanged files which are not found in the 'chezmoi status' output.",
        disabled_tooltip=None,
    )
    unmanaged_dirs = SwitchData(
        label=SwitchLabel.unmanaged_dirs,
        enabled_tooltip="The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
        disabled_tooltip=None,
    )
    unwanted = SwitchData(
        label=SwitchLabel.unwanted,
        enabled_tooltip="Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
        disabled_tooltip=None,
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip

    @property
    def disabled_tooltip(self) -> str | None:
        return self.value.disabled_tooltip
