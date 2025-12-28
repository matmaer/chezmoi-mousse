"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OpButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

from ._app_state import AppState
from ._chezmoi_command import WriteCmd

__all__ = ["OpBtnLabels", "OpBtnEnum"]


class OpBtnLabels(StrEnum):
    add_dir_run = "Run Chezmoi Add Dir"
    add_dir_review = "Review Add Dir"
    add_file_run = "Run Chezmoi Add File"
    add_file_review = "Review Add File"
    apply_review = "Review Apply"
    apply_run = "Run Chezmoi Apply"
    cancel = "Cancel"
    destroy_run = "Run Chezmoi Destroy"
    destroy_review = "Review Destroy"
    exit_app = "Exit App"
    forget_run = "Run Chezmoi Forget"
    forget_review = "Review Forget"
    init_clone = "Init Clone Repo"
    init_new = "Init New Repo"
    re_add_review = "Review Re-Add"
    re_add_run = "Run Chezmoi Re-Add"
    reload = "Reload"


@dataclass(slots=True)
class OpBtnData:
    label: str
    cmd_live: WriteCmd | None = None
    cmd_dry: WriteCmd | None = None


class OpBtnEnum(Enum):
    add_file = OpBtnData(
        label=OpBtnLabels.add_file_review,
        cmd_dry=WriteCmd.add_dry,
        cmd_live=WriteCmd.add_live,
    )
    add_dir = OpBtnData(
        label=OpBtnLabels.add_dir_review,
        cmd_dry=WriteCmd.add_dry,
        cmd_live=WriteCmd.add_live,
    )
    apply_path = OpBtnData(
        cmd_dry=WriteCmd.apply_dry,
        cmd_live=WriteCmd.apply_live,
        label=OpBtnLabels.apply_review,
    )
    re_add_path = OpBtnData(
        cmd_dry=WriteCmd.re_add_dry,
        cmd_live=WriteCmd.re_add_live,
        label=OpBtnLabels.re_add_review,
    )
    forget_path = OpBtnData(
        label=OpBtnLabels.forget_review,
        cmd_dry=WriteCmd.forget_dry,
        cmd_live=WriteCmd.forget_live,
    )
    destroy_path = OpBtnData(
        label=OpBtnLabels.destroy_review,
        cmd_dry=WriteCmd.destroy_dry,
        cmd_live=WriteCmd.destroy_live,
    )
    init_new = OpBtnData(label=OpBtnLabels.init_new)
    init_clone = OpBtnData(label=OpBtnLabels.init_clone)
    operate_exit = OpBtnData(label=OpBtnLabels.cancel)

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def _cmd_live(self) -> WriteCmd:
        if self.value.cmd_live is None:
            raise ValueError(f"No live command for button {self.name}")
        return self.value.cmd_live

    @property
    def _cmd_dry(self) -> WriteCmd:
        if self.value.cmd_dry is None:
            raise ValueError(f"No dry command for button {self.name}")
        return self.value.cmd_dry

    @property
    def write_cmd(self) -> WriteCmd:

        if AppState.changes_enabled():
            return self._cmd_live
        else:
            return self._cmd_dry
