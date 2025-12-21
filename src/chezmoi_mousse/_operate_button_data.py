"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OperateButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

__all__ = ["OperateBtn"]


# Sentinel value to distinguish "not provided" from None
_UNSET = "UNSET"


class OpBtnLabels(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_dir = "Apply Dir"
    apply_file = "Apply File"
    apply_path = "Apply Path"
    destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    destroy_path = "Destroy Path"
    forget_dir = "Forget Dir"
    forget_file = "Forget File"
    forget_path = "Forget Path"
    init_clone_repo = "Init Clone Repo"
    init_new_repo = "Init New Repo"
    cancel = "Cancel"
    exit_app = "Exit App"
    reload = "Reload"
    re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"
    re_add_path = "Re-Add Path"


class OpBtnToolTips(StrEnum):
    in_dest_dir = "This is the destDir, select a path to operate on."
    path_no_status = "The selected path has no status to operate on."
    review = "Review changes before running the command."
    add_file_disabled = "Select a file to enable."
    add_dir_disabled = "Select a directory to enable."


@dataclass(slots=True)
class OpBtnData:

    initial_label: str
    initial_tooltip: str | None

    # Path-specific labels and tooltips
    file_label: str = _UNSET
    dir_label: str = _UNSET

    # Add and Init button specific
    disabled_tooltip: str = _UNSET

    # Init button specific
    init_new_label: str = _UNSET
    init_clone_label: str = _UNSET


class OperateBtn(Enum):
    add_file = OpBtnData(
        disabled_tooltip=OpBtnToolTips.add_file_disabled,
        file_label=OpBtnLabels.add_file,
        initial_label=OpBtnLabels.add_file,
        initial_tooltip=OpBtnToolTips.in_dest_dir,
    )
    add_dir = OpBtnData(
        dir_label=OpBtnLabels.add_dir,
        disabled_tooltip="Select a directory to operate on.",
        initial_label=OpBtnLabels.add_dir,
        initial_tooltip=OpBtnToolTips.in_dest_dir,
    )
    apply_path = OpBtnData(
        dir_label=OpBtnLabels.apply_dir,
        disabled_tooltip=OpBtnToolTips.path_no_status,
        file_label=OpBtnLabels.apply_file,
        initial_label=OpBtnLabels.apply_path,
        initial_tooltip=OpBtnToolTips.in_dest_dir,
    )
    re_add_path = OpBtnData(
        dir_label=OpBtnLabels.re_add_dir,
        disabled_tooltip=OpBtnToolTips.path_no_status,
        file_label=OpBtnLabels.re_add_file,
        initial_label=OpBtnLabels.re_add_path,
        initial_tooltip=OpBtnToolTips.in_dest_dir,
    )
    forget_path = OpBtnData(
        dir_label=OpBtnLabels.forget_dir,
        file_label=OpBtnLabels.forget_file,
        initial_label=OpBtnLabels.forget_path,
        initial_tooltip=OpBtnToolTips.in_dest_dir,
    )
    destroy_path = OpBtnData(
        dir_label="Destroy Dir",
        file_label="Destroy File",
        initial_label="Destroy Path",
        initial_tooltip=OpBtnToolTips.in_dest_dir,
    )
    init_repo = OpBtnData(
        disabled_tooltip="Provide an input to determine the repository to clone from.",
        init_clone_label="Init Clone Repo",
        init_new_label="Init New Repo",
        initial_label="Init New Repo",
        initial_tooltip="Initialize a new chezmoi repository in your home directory with default settings.",
    )
    operate_exit = OpBtnData(initial_label="Cancel", initial_tooltip=None)

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def initial_label(self) -> str:
        return self.value.initial_label

    @property
    def initial_tooltip(self) -> str | None:
        return self.value.initial_tooltip

    # Exit button specific attribute access

    @property
    def cancel_label(self) -> str:
        return OpBtnLabels.cancel.value

    @property
    def exit_app_label(self) -> str:
        return OpBtnLabels.exit_app.value

    @property
    def reload_label(self) -> str:
        return OpBtnLabels.reload.value

    # AddTab button specific attribute access

    @property
    def disabled_tooltip(self) -> str:
        return self.value.disabled_tooltip

    # Apply and ReAdd tab specific attribute access

    @property
    def file_label(self) -> str:
        return self.value.file_label

    @property
    def dir_label(self) -> str:
        return self.value.dir_label

    @property
    def init_new_label(self) -> str:
        return self.value.init_new_label

    @property
    def init_clone_label(self) -> str:
        return self.value.init_clone_label
