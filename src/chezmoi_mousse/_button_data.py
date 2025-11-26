"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OperateButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from ._str_enums import PathKind


__all__ = ["FlatBtn", "LinkBtn", "OperateBtn", "TabBtn"]


# Sentinel value to distinguish "not provided" from None
_UNSET = "UNSET"


class FlatBtn(StrEnum):
    add_help = "Add Help"
    apply_help = "Apply Help"
    cat_config = "Cat Config"
    diagram = "Diagram"
    doctor = "Doctor"
    exit_app = "Exit App"
    ignored = "Ignored"
    clone_repo = "Init Clone"
    new_repo = "Chezmoi Init"
    pw_mgr_info = "Password Managers"
    re_add_help = "Re-Add Help"
    template_data = "Template Data"


class LinkBtn(StrEnum):
    chezmoi_add = "https://www.chezmoi.io/reference/commands/add/"
    chezmoi_apply = "https://www.chezmoi.io/reference/commands/apply/"
    chezmoi_destroy = "https://www.chezmoi.io/reference/commands/destroy/"
    chezmoi_forget = "https://www.chezmoi.io/reference/commands/forget/"
    chezmoi_install = "https://www.chezmoi.io/install/"
    chezmoi_re_add = "https://www.chezmoi.io/reference/commands/re-add/"

    @property
    def link_url(self) -> str:
        return self.value

    @property
    def link_text(self) -> str:
        return (
            self.value.replace("https://", "").replace("www.", "").rstrip("/")
        )


class TabBtn(StrEnum):
    # Tab buttons for content switcher within a main tab
    app_log = "App"
    contents = "Contents"
    debug_log = "Debug"
    diff = "Diff"
    git_log_global = "Git"
    git_log_path = "Git-Log"
    list = "List"
    operate_log = "Operate"
    read_log = "Read"
    tree = "Tree"


class SharedLabels(StrEnum):
    cancel = "Cancel"
    close = "Close"
    exit_app = "Exit App"


class SharedToolTips(StrEnum):
    dir_no_status = "The selected directory has no status to operate on."
    file_no_status = "The selected file has no status to operate on."
    in_dest_dir = "This is the destDir, select a path to operate on."


@dataclass(slots=True)
class OperateButtonData:
    # Fields set to UNSET will raise AttributeError when accessed, ensures IDE shows available fields.

    initial_label: str
    initial_tooltip: str = _UNSET

    # Path-specific labels and tooltips
    file_label: str = _UNSET
    dir_label: str = _UNSET
    file_tooltip: str = _UNSET
    dir_tooltip: str = _UNSET
    file_no_status_tooltip: str = _UNSET
    dir_no_status_tooltip: str = _UNSET

    # Add button specific
    enabled_tooltip: str = _UNSET
    disabled_tooltip: str = _UNSET

    # Exit button specific
    cancel_label: str = SharedLabels.cancel.value
    close_label: str = SharedLabels.close.value
    close_tooltip: str = _UNSET
    exit_app_label: str = SharedLabels.exit_app.value
    exit_app_tooltip: str = _UNSET

    # Init screen specific
    init_new_label: str = _UNSET
    init_new_tooltip: str = _UNSET
    init_clone_label: str = _UNSET
    init_clone_tooltip: str = _UNSET


class OperateBtn(Enum):
    add_file = OperateButtonData(
        initial_label="Add File",
        initial_tooltip=SharedToolTips.in_dest_dir.value,
        file_label="Add File",
        disabled_tooltip="Select a file to operate on.",
        enabled_tooltip="Manage the file with chezmoi.",
    )
    add_dir = OperateButtonData(
        initial_label="Add Dir",
        initial_tooltip=SharedToolTips.in_dest_dir.value,
        dir_label="Add Dir",
        disabled_tooltip="Select a directory to operate on.",
        enabled_tooltip="Manage the directory with chezmoi.",
    )
    apply_path = OperateButtonData(
        initial_label="Apply Path",
        initial_tooltip=SharedToolTips.in_dest_dir.value,
        dir_label="Apply Dir",
        dir_no_status_tooltip=SharedToolTips.dir_no_status.value,
        dir_tooltip='Run "chezmoi apply" on the directory.',
        file_label="Apply File",
        file_no_status_tooltip=SharedToolTips.file_no_status.value,
        file_tooltip='Run "chezmoi apply" on the file.',
    )
    re_add_path = OperateButtonData(
        initial_label="Re-Add Path",
        initial_tooltip=SharedToolTips.in_dest_dir.value,
        dir_label="Re-Add Dir",
        dir_no_status_tooltip=SharedToolTips.dir_no_status.value,
        dir_tooltip='Run "chezmoi re-add" on the directory.',
        file_label="Re-Add File",
        file_no_status_tooltip=SharedToolTips.file_no_status.value,
        file_tooltip='Run "chezmoi re-add" on the file.',
    )
    forget_path = OperateButtonData(
        initial_label="Forget Path",
        initial_tooltip=SharedToolTips.in_dest_dir.value,
        dir_label="Forget Dir",
        dir_tooltip='Run "chezmoi forget", stop managing the directory.',
        file_label="Forget File",
        file_tooltip='Run "chezmoi forget", stop managing the file.',
    )
    destroy_path = OperateButtonData(
        initial_label="Destroy Path",
        initial_tooltip=SharedToolTips.in_dest_dir.value,
        dir_label="Destroy Dir",
        dir_tooltip='Run "chezmoi destroy" on the directory. Permanently remove the directory and its files from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!',
        file_label="Destroy File",
        file_tooltip='Run "chezmoi destroy" on the file. Permanently remove the file from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!',
    )
    init_new_repo = OperateButtonData(
        initial_label="Chezmoi Init New Repo",
        initial_tooltip="Initialize a new chezmoi repository in your home directory with default settings shown in the cat config section.",
        init_new_label="Chezmoi Init New Repo",
        init_new_tooltip="Initialize a new chezmoi repository in your home directory with default settings shown in the cat config section.",
    )
    init_clone_repo = OperateButtonData(
        initial_label="Chezmoi Init Clone Repo",
        initial_tooltip="Initialize a the chezmoi repository by cloning from a provided remote repository.",
        init_clone_label="Chezmoi Init Clone Repo",
        init_clone_tooltip="Initialize a the chezmoi repository by cloning from a provided remote repository.",
    )
    init_exit = OperateButtonData(
        initial_label=SharedLabels.exit_app.value,
        initial_tooltip="Exit application. Cannot run the main application without an initialized chezmoi state, init a new repository, or init from a remote repository.",
        exit_app_tooltip="Exit application. Cannot run the main application without an initialized chezmoi state, init a new repository, or init from a remote repository.",
        close_tooltip="Reload the application to load the initialized chezmoi state.",
    )
    operate_exit = OperateButtonData(initial_label=SharedLabels.cancel.value)

    # Allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def initial_label(self) -> str:
        return self.value.initial_label

    @property
    def initial_tooltip(self) -> str:
        return self.value.initial_tooltip

    # Exit button specific attribute access

    @property
    def cancel_label(self) -> str:
        return self.value.cancel_label

    @property
    def close_label(self) -> str:
        return self.value.close_label

    @property
    def exit_app_label(self) -> str:
        return self.value.exit_app_label

    @property
    def close_tooltip(self) -> str:
        return self.value.close_tooltip

    @property
    def exit_app_tooltip(self) -> str:
        return self.value.exit_app_tooltip

    # Init screen specific attribute access

    @property
    def init_new_label(self) -> str:
        return self.value.init_new_label

    @property
    def init_new_tooltip(self) -> str:
        return self.value.init_new_tooltip

    @property
    def init_clone_label(self) -> str:
        return self.value.init_clone_label

    @property
    def init_clone_tooltip(self) -> str:
        return self.value.init_clone_tooltip

    # AddTab button specific attribute access

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip

    @property
    def disabled_tooltip(self) -> str:
        return self.value.disabled_tooltip

    # Apply and ReAdd tab specific attribute access

    @property
    def file_no_status_tooltip(self) -> str:
        return self.value.file_no_status_tooltip

    @property
    def dir_no_status_tooltip(self) -> str:
        return self.value.dir_no_status_tooltip

    # Dir/File button specific attribute access

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

    # General methods

    def label(self, path_type: "PathKind") -> str:
        if path_type == "dir":
            return self.dir_label
        elif path_type == "file":
            return self.file_label
        else:
            raise ValueError("path_type must be 'dir' or 'file'")

    def tooltip(self, path_type: "PathKind") -> str:
        if path_type == "dir":
            return self.dir_tooltip
        elif path_type == "file":
            return self.file_tooltip
        else:
            raise ValueError("path_type must be 'dir', 'file', or None")

    @classmethod
    def from_label(cls, label: str) -> "OperateBtn":
        for member in cls:
            if member.value.file_label == label:
                return member
            if member.value.dir_label == label:
                return member
            if member.value.initial_label == label:
                return member
        raise ValueError(f"{cls.__name__} has no member with label={label}")
