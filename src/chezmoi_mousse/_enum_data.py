from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import TYPE_CHECKING

from ._chezmoi_command import WriteCmd
from ._str_enum_names import ScreenName, TabName
from ._str_enums import OpBtnLabel, OperateString, SwitchLabel

if TYPE_CHECKING:
    from ._app_ids import AppIds

__all__ = ["OpBtnEnum", "SwitchEnum"]


@dataclass(slots=True)
class OpBtnData:
    label: str
    write_cmd: WriteCmd
    info_strings: list[str] | None = None
    info_sub_title: str | None = None
    info_title: str | None = None


class OpBtnEnum(Enum):
    _add_review = OpBtnData(label=OpBtnLabel.add_review, write_cmd=WriteCmd.add)
    _add_run = OpBtnData(
        label=OpBtnLabel.add_run,
        write_cmd=WriteCmd.add,
        info_strings=[OperateString.add_path_info],
        info_sub_title=OperateString.add_subtitle,
        info_title=OperateString.run_completed_dry,
    )
    _apply_review = OpBtnData(
        label=OpBtnLabel.apply_review,
        write_cmd=WriteCmd.apply,
        info_strings=[OperateString.apply_path_info],
        info_sub_title=OperateString.apply_subtitle,
        info_title=OperateString.ready_to_run,
    )
    _apply_run = OpBtnData(
        label=OpBtnLabel.apply_run,
        write_cmd=WriteCmd.apply,
        info_strings=[OperateString.apply_path_info],
        info_sub_title=OperateString.apply_subtitle,
        info_title=OperateString.run_completed_dry,
    )
    _destroy_review = OpBtnData(
        label=OpBtnLabel.destroy_review,
        write_cmd=WriteCmd.destroy,
        info_strings=[OperateString.destroy_path_info],
        info_sub_title=OperateString.destroy_subtitle,
        info_title=OperateString.ready_to_run,
    )
    _destroy_run = OpBtnData(
        label=OpBtnLabel.destroy_run,
        write_cmd=WriteCmd.destroy,
        info_strings=[OperateString.destroy_path_info],
        info_sub_title=OperateString.destroy_subtitle,
        info_title=OperateString.run_completed_dry,
    )
    _forget_review = OpBtnData(
        label=OpBtnLabel.forget_review,
        write_cmd=WriteCmd.forget,
        info_strings=[OperateString.forget_path_info],
        info_sub_title=OperateString.forget_subtitle,
        info_title=OperateString.ready_to_run,
    )
    _forget_run = OpBtnData(
        label=OpBtnLabel.forget_run,
        write_cmd=WriteCmd.forget,
        info_strings=[OperateString.forget_path_info],
        info_sub_title=OperateString.forget_subtitle,
        info_title=OperateString.run_completed_dry,
    )
    _re_add_review = OpBtnData(
        label=OpBtnLabel.re_add_review,
        write_cmd=WriteCmd.re_add,
        info_strings=[OperateString.re_add_path_info],
        info_sub_title=OperateString.re_add_subtitle,
        info_title=OperateString.ready_to_run,
    )
    _re_add_run = OpBtnData(
        label=OpBtnLabel.re_add_run,
        write_cmd=WriteCmd.re_add,
        info_strings=[OperateString.re_add_path_info],
        info_sub_title=OperateString.re_add_subtitle,
        info_title=OperateString.run_completed_dry,
    )
    _init = OpBtnData(
        label=OpBtnLabel.init_review,
        write_cmd=WriteCmd.init_new,
        info_strings=[OperateString.init_new_info],
        info_sub_title=OperateString.init_subtitle,
        info_title=OperateString.ready_to_run,
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

    @classmethod
    @cache
    def op_btn_enum_dict(cls, ids: "AppIds") -> dict[str, "OpBtnEnum | OpBtnLabel"]:
        if ids.canvas_name == ScreenName.init:
            return {
                ids.op_btn.init: cls._init,
                ids.op_btn.exit_app: OpBtnLabel.exit_app,
            }
        if ids.canvas_name != TabName.add:
            _btn_dict = {
                ids.op_btn.forget_review: cls._forget_review,
                ids.op_btn.forget_run: cls._forget_run,
                ids.op_btn.destroy_review: cls._destroy_review,
                ids.op_btn.destroy_run: cls._destroy_run,
            }
            if ids.canvas_name == TabName.apply:
                _btn_dict = {
                    ids.op_btn.apply_review: cls._apply_review,
                    ids.op_btn.apply_run: cls._apply_run,
                    **_btn_dict,
                }
            if ids.canvas_name == TabName.re_add:
                _btn_dict = {
                    ids.op_btn.re_add_review: cls._re_add_review,
                    ids.op_btn.re_add_run: cls._re_add_run,
                    **_btn_dict,
                }
        else:  # Add tab
            _btn_dict = {
                ids.op_btn.add_review: cls._add_review,
                ids.op_btn.add_run: cls._add_run,
            }
        return {
            **_btn_dict,
            ids.op_btn.cancel: OpBtnLabel.cancel,
            ids.op_btn.reload: OpBtnLabel.reload,
        }

    @classmethod
    @cache
    def review_to_run(cls, btn_label: OpBtnLabel) -> "OpBtnEnum":
        _mapping = {
            OpBtnLabel.add_review: cls._add_run,
            OpBtnLabel.apply_review: cls._apply_run,
            OpBtnLabel.destroy_review: cls._destroy_run,
            OpBtnLabel.forget_review: cls._forget_run,
            OpBtnLabel.re_add_review: cls._re_add_run,
        }
        return _mapping[btn_label]

    @classmethod
    @cache
    def review_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls._add_review,
            cls._apply_review,
            cls._destroy_review,
            cls._forget_review,
            cls._re_add_review,
        }

    @classmethod
    @cache
    def run_btn_enums(cls) -> set["OpBtnEnum"]:
        return {
            cls._add_run,
            cls._apply_run,
            cls._destroy_run,
            cls._forget_run,
            cls._re_add_run,
        }


@dataclass(frozen=True, slots=True)
class SwitchData:
    label: str
    enabled_tooltip: str
    disabled_tooltip: str | None


class SwitchEnum(Enum):

    init_repo_switch = SwitchData(
        label=SwitchLabel.init_repo,
        enabled_tooltip=(
            "Initialize a new chezmoi repository, or clone an existing remote "
            "chezmoi repository."
        ),
        disabled_tooltip=None,
    )
    expand_all = SwitchData(
        label=SwitchLabel.expand_all,
        enabled_tooltip=(
            "Expand all managed directories. Showing unchanged depending on the "
            '"show unchanged files" switch.'
        ),
        disabled_tooltip="Switch to Tree to enable this switch.",
    )
    unchanged = SwitchData(
        label=SwitchLabel.unchanged,
        enabled_tooltip=(
            "Include unchanged paths which are not found in the "
            "'chezmoi status' output."
        ),
        disabled_tooltip=None,
    )
    unmanaged_dirs = SwitchData(
        label=SwitchLabel.unmanaged_dirs,
        enabled_tooltip=(
            "The default (disabled), only shows directories which already "
            "contain managed files. This allows spotting new unmanaged files in "
            "already managed directories. Enable to show all directories which contain "
            "unmanaged files."
        ),
        disabled_tooltip=None,
    )
    unwanted = SwitchData(
        label=SwitchLabel.unwanted,
        enabled_tooltip=(
            "Include files and directories considered as 'unwanted' for a dotfile "
            "manager. These include cache, temporary, trash (recycle bin) and other "
            "similar files or directories."
        ),
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
