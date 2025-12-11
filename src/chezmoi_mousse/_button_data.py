"""This module does not import anything from textual, it only contains classes
imported at module init before launching the textual app, and attributes
accessed after the app is launched.

The initial_label attribute is used to construct the OperateButton class in
shared/_buttons.py.
"""

from dataclasses import dataclass
from enum import Enum, StrEnum

from ._str_enums import BindingDescription

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
    init_clone = "Init Clone"
    init_new = "Init New"
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

    # Exit button specific
    cancel_label: str = SharedLabels.cancel
    close_label: str = SharedLabels.close
    close_tooltip: str | None = None
    exit_app_label: str = SharedLabels.exit_app
    exit_app_tooltip: str | None = None
    reload_label: str = BindingDescription.reload.value
    reload_tooltip: str = (
        "Reload the application to load the initialized chezmoi state."
    )


class OperateBtn(Enum):
    add_file = OpBtnData(
        initial_label="Add File",
        initial_tooltip=SharedToolTips.in_dest_dir,
        file_label="Add File",
        disabled_tooltip="Select a file to operate on.",
        enabled_tooltip="Manage the file with chezmoi.",
    )
    add_dir = OpBtnData(
        initial_label="Add Dir",
        initial_tooltip=SharedToolTips.in_dest_dir,
        dir_label="Add Dir",
        disabled_tooltip="Select a directory to operate on.",
        enabled_tooltip="Manage the directory with chezmoi.",
    )
    apply_path = OpBtnData(
        initial_label="Apply Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
        dir_label="Apply Dir",
        disabled_tooltip=SharedToolTips.path_no_status,
        dir_tooltip='Run "chezmoi apply" on the directory.',
        file_label="Apply File",
        file_tooltip='Run "chezmoi apply" on the file.',
    )
    re_add_path = OpBtnData(
        initial_label="Re-Add Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
        dir_label="Re-Add Dir",
        dir_tooltip='Run "chezmoi re-add" on the directory.',
        file_label="Re-Add File",
        disabled_tooltip=SharedToolTips.path_no_status,
        file_tooltip='Run "chezmoi re-add" on the file.',
    )
    forget_path = OpBtnData(
        initial_label="Forget Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
        dir_label="Forget Dir",
        dir_tooltip='Run "chezmoi forget", stop managing the directory.',
        file_label="Forget File",
        file_tooltip='Run "chezmoi forget", stop managing the file.',
    )
    destroy_path = OpBtnData(
        initial_label="Destroy Path",
        initial_tooltip=SharedToolTips.in_dest_dir,
        dir_label="Destroy Dir",
        dir_tooltip='Run "chezmoi destroy" on the directory. Permanently remove the directory and its files from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!',
        file_label="Destroy File",
        file_tooltip='Run "chezmoi destroy" on the file. Permanently remove the file from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!',
    )
    init_repo = OpBtnData(
        initial_label="Init New Repo",
        initial_tooltip="Initialize a new chezmoi repository in your home directory with default settings.",
        init_new_label="Init New Repo",
        init_clone_label="Init Clone Repo",
        enabled_tooltip="Valid URL entered, ready to clone.",
        disabled_tooltip="Provide an input to determine the repository to clone from.",
    )
    operate_exit = OpBtnData(
        initial_label=SharedLabels.cancel, initial_tooltip=None
    )

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
        return self.value.cancel_label

    @property
    def close_label(self) -> str:
        return self.value.close_label

    @property
    def exit_app_label(self) -> str:
        return self.value.exit_app_label

    @property
    def close_tooltip(self) -> str | None:
        return self.value.close_tooltip

    @property
    def exit_app_tooltip(self) -> str | None:
        return self.value.exit_app_tooltip

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
    def reload_label(self) -> str:
        return self.value.reload_label

    @property
    def reload_tooltip(self) -> str:
        return self.value.reload_tooltip

    @property
    def init_new_label(self) -> str:
        return self.value.init_new_label

    @property
    def init_clone_label(self) -> str:
        return self.value.init_clone_label
