"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OperateButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

from ._switch_data import SwitchLabel

__all__ = ["OpBtnLabels", "OpBtnToolTips", "OperateBtn"]


class OpBtnLabels(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_dir = "Apply Dir"
    apply_file = "Apply File"
    apply_path = "Apply Path"
    cancel = "Cancel"
    destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    destroy_path = "Destroy Path"
    exit_app = "Exit App"
    forget_dir = "Forget Dir"
    forget_file = "Forget File"
    forget_path = "Forget Path"
    init_clone = "Init Clone Repo"
    init_new = "Init New Repo"
    re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"
    re_add_path = "Re-Add Path"
    reload = "Reload"


class OpBtnToolTips(StrEnum):
    add_dir_disabled = "Select a directory to enable."
    add_file_disabled = "Select a file to enable."
    in_dest_dir = "This is the destDir, select a path to operate on."
    init_clone_disabled = (
        f"Provide an input to enable {OpBtnLabels.init_clone}."
    )
    init_clone_switch_off = (
        f"Switch the {SwitchLabel.init_repo} switch on to "
        f"enable {OpBtnLabels.init_clone}."
    )
    init_new_disabled = (
        f"Switch the {SwitchLabel.init_repo} switch off to "
        f"enable {OpBtnLabels.init_new}."
    )
    path_no_status = "The selected path has no status to operate on."
    review = "Review changes before running the command."


@dataclass(slots=True)
class OpBtnData:
    label: str
    tooltip: str | None


class OperateBtn(Enum):
    add_file = OpBtnData(
        label=OpBtnLabels.add_file, tooltip=OpBtnToolTips.in_dest_dir
    )
    add_dir = OpBtnData(
        label=OpBtnLabels.add_dir, tooltip=OpBtnToolTips.in_dest_dir
    )
    apply_path = OpBtnData(
        label=OpBtnLabels.apply_path, tooltip=OpBtnToolTips.in_dest_dir
    )
    re_add_path = OpBtnData(
        label=OpBtnLabels.re_add_path, tooltip=OpBtnToolTips.in_dest_dir
    )
    forget_path = OpBtnData(
        label=OpBtnLabels.forget_path, tooltip=OpBtnToolTips.in_dest_dir
    )
    destroy_path = OpBtnData(
        label=OpBtnLabels.destroy_path, tooltip=OpBtnToolTips.in_dest_dir
    )
    init_new = OpBtnData(label=OpBtnLabels.init_new, tooltip=None)
    init_clone = OpBtnData(
        label=OpBtnLabels.init_clone,
        tooltip=OpBtnToolTips.init_clone_switch_off,
    )
    operate_exit = OpBtnData(label=OpBtnLabels.cancel, tooltip=None)

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def tooltip(self) -> str | None:
        return self.value.tooltip
