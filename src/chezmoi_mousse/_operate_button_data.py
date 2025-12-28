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
    cmd_live: WriteCmd | None = None
    cmd_dry: WriteCmd | None = None


class OpBtnEnum(Enum):
    add = OpBtnData(
        label=OpBtnLabels.add_review,
        cmd_dry=WriteCmd.add_dry,
        cmd_live=WriteCmd.add_live,
    )
    apply = OpBtnData(
        cmd_dry=WriteCmd.apply_dry,
        cmd_live=WriteCmd.apply_live,
        label=OpBtnLabels.apply_review,
    )
    destroy = OpBtnData(
        label=OpBtnLabels.destroy_review,
        cmd_dry=WriteCmd.destroy_dry,
        cmd_live=WriteCmd.destroy_live,
    )
    forget = OpBtnData(
        label=OpBtnLabels.forget_review,
        cmd_dry=WriteCmd.forget_dry,
        cmd_live=WriteCmd.forget_live,
    )
    re_add = OpBtnData(
        cmd_dry=WriteCmd.re_add_dry,
        cmd_live=WriteCmd.re_add_live,
        label=OpBtnLabels.re_add_review,
    )
    init = OpBtnData(label=OpBtnLabels.init_review)

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
