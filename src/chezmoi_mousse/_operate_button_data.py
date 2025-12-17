"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OperateButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

from ._str_enum_bindings import BindingDescription

__all__ = ["OperateBtn"]


# Sentinel value to distinguish "not provided" from None
_UNSET = "UNSET"


class SharedToolTips(StrEnum):
    path_no_status = "The selected path has no status to operate on."
    in_dest_dir = "This is the destDir, select a path to operate on."


@dataclass(slots=True)
class OpBtnData:

    initial_label: str
    initial_tooltip: str | None

    # Path-specific labels and tooltips
    file_label: str = _UNSET
    dir_label: str = _UNSET
    file_tooltip: str = _UNSET
    dir_tooltip: str = _UNSET

    # Add and Init button specific
    enabled_tooltip: str = _UNSET
    disabled_tooltip: str = _UNSET

    # Init button specific
    init_new_label: str = _UNSET
    init_clone_label: str = _UNSET


class OperateBtn(Enum):
    add_file = OpBtnData(
        disabled_tooltip="Select a file to operate on.",
        enabled_tooltip="Manage the file with chezmoi.",
        file_label="Add File",
        initial_label="Add File",
        initial_tooltip=SharedToolTips.in_dest_dir,
    )
    add_dir = OpBtnData(
        dir_label="Add Dir",
        disabled_tooltip="Select a directory to operate on.",
        enabled_tooltip="Manage the directory with chezmoi.",
        initial_label="Add Dir",
        initial_tooltip=SharedToolTips.in_dest_dir,
    )
    apply_path = OpBtnData(
        dir_label="Apply Dir",
        dir_tooltip='Run "chezmoi apply" on the directory.',
        disabled_tooltip=SharedToolTips.path_no_status,
        file_label="Apply File",
        file_tooltip='Run "chezmoi apply" on the file.',
        initial_label="Apply Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
    )
    re_add_path = OpBtnData(
        dir_label="Re-Add Dir",
        dir_tooltip='Run "chezmoi re-add" on the directory.',
        disabled_tooltip=SharedToolTips.path_no_status,
        file_label="Re-Add File",
        file_tooltip='Run "chezmoi re-add" on the file.',
        initial_label="Re-Add Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
    )
    forget_path = OpBtnData(
        dir_label="Forget Dir",
        dir_tooltip='Run "chezmoi forget", stop managing the directory.',
        file_label="Forget File",
        file_tooltip='Run "chezmoi forget", stop managing the file.',
        initial_label="Forget Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
    )
    destroy_path = OpBtnData(
        dir_label="Destroy Dir",
        dir_tooltip='Run "chezmoi destroy" on the directory. Permanently remove the directory and its files from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!',
        file_label="Destroy File",
        file_tooltip='Run "chezmoi destroy" on the file. Permanently remove the file from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!',
        initial_label="Destroy Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
    )
    init_repo = OpBtnData(
        disabled_tooltip="Provide an input to determine the repository to clone from.",
        enabled_tooltip="Valid URL entered, ready to clone.",
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
        return "Cancel"

    @property
    def exit_app_label(self) -> str:
        return "Exit App"

    @property
    def reload_label(self) -> str:
        return BindingDescription.reload.value

    # AddTab button specific attribute access

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip

    @property
    def disabled_tooltip(self) -> str:
        return self.value.disabled_tooltip

    # Apply and ReAdd tab specific attribute access

    @property
    def dir_tooltip(self) -> str:
        return self.value.dir_tooltip

    @property
    def file_tooltip(self) -> str:
        return self.value.file_tooltip

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
