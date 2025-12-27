"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OperateButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

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


class OpBtnEnum(Enum):
    add_file = OpBtnData(label=OpBtnLabels.add_file_review)
    add_dir = OpBtnData(label=OpBtnLabels.add_dir_review)
    apply_path = OpBtnData(label=OpBtnLabels.apply_review)
    re_add_path = OpBtnData(label=OpBtnLabels.re_add_review)
    forget_path = OpBtnData(label=OpBtnLabels.forget_review)
    destroy_path = OpBtnData(label=OpBtnLabels.destroy_review)
    init_new = OpBtnData(label=OpBtnLabels.init_new)
    init_clone = OpBtnData(label=OpBtnLabels.init_clone)
    operate_exit = OpBtnData(label=OpBtnLabels.cancel)

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label
