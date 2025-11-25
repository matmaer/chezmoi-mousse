from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from ._str_enums import PathKind

__all__ = ["FlatBtn", "LinkBtn", "OperateBtn", "TabBtn"]


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


class OpBtn(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_dir = "Apply Dir"
    apply_file = "Apply File"
    apply_path = "Apply Path"
    cancel = "Cancel"
    close = "Close"
    destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    destroy_path = "Destroy Path"
    exit_app = "Exit App"
    forget_dir = "Forget Dir"
    forget_file = "Forget File"
    forget_path = "Forget Path"
    re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"
    re_add_path = "Re-Add Path"


class ToolTips(StrEnum):
    add_dir = "Manage the directory with chezmoi."
    add_dir_disabled = "Select a directory to operate on."
    add_file = "Manage the file with chezmoi."
    add_file_disabled = "Select a file to operate on."
    apply_dir = 'Run "chezmoi apply" on the directory.'
    apply_file = 'Run "chezmoi apply" on the file.'
    destroy_dir = 'Run "chezmoi destroy" on the directory. Permanently remove the directory and its files from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!'
    destroy_file = 'Run "chezmoi destroy" on the file. Permanently remove the file from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!'
    dir_no_status = "The selected directory has no status to operate on."
    file_no_status = "The selected file has no status to operate on."
    forget_dir = 'Run "chezmoi forget", stop managing the directory.'
    forget_file = 'Run "chezmoi forget", stop managing the file.'
    initial = "This is the destDir, select a path to operate on."
    re_add_dir = 'Run "chezmoi re-add" on the directory.'
    re_add_file = 'Run "chezmoi re-add" on the file.'


@dataclass(slots=True)
class ApplyReAddButtonData:
    dir_label: str
    dir_no_status_tooltip: str
    dir_tooltip: str
    file_label: str
    file_no_status_tooltip: str
    file_tooltip: str
    initial_label: str


@dataclass(slots=True)
class DestroyForgetButtonData:
    # We don't need status tooltips here
    dir_label: str
    dir_tooltip: str
    file_label: str
    file_tooltip: str
    initial_label: str  # this is the label containing "Path"


@dataclass(slots=True)
class AddButtonData:
    # We don't need status tooltips here
    disabled_tooltip: str
    enabled_tooltip: str
    initial_label: str


@dataclass(slots=True)
class InitScreenNewRepositoryButtonData:
    init_new_label: str = "Chezmoi Init New Repo"
    init_new_tooltip: str = (
        "Initialize a new chezmoi repository in your home directory with default settings shown in the cat config section."
    )
    initial_label: str = init_new_label  # used by the OperateButton class


@dataclass(slots=True)
class InitScreenCloneRepositoryButtonData:
    init_clone_label: str = "Chezmoi Init Clone Repo"
    init_clone_tooltip: str = (
        "Initialize a the chezmoi repository by cloning from a provided remote repository."
    )
    initial_label: str = init_clone_label  # used by the OperateButton class


@dataclass(slots=True)
class InitScreenExitButtonData:
    exit_app_label: str = OpBtn.exit_app.value
    exit_app_tooltip: str = (
        "Ext application. Cannot run the main application without an initialized chezmoi state, init a new repository, or init from a remote repository."
    )
    close_label: str = OpBtn.operate_close.value
    close_tooltip: str = (
        "Restart the application to load the initialized chezmoi state."
    )
    initial_label: str = exit_app_label  # used by the OperateButton class


@dataclass(slots=True)
class OperateScreenExitButtonData:
    cancel_label: str
    close_label: str
    initial_label: str


class OperateBtn(Enum):
    add_file = AddButtonData(
        disabled_tooltip=ToolTips.add_file_disabled.value,
        enabled_tooltip=ToolTips.add_file.value,
        initial_label=OpBtn.add_file.value,
    )
    add_dir = AddButtonData(
        disabled_tooltip=ToolTips.add_dir_disabled.value,
        enabled_tooltip=ToolTips.add_dir.value,
        initial_label=OpBtn.add_dir.value,
    )
    apply_path = ApplyReAddButtonData(
        dir_label=OpBtn.apply_dir.value,
        dir_no_status_tooltip=ToolTips.dir_no_status.value,
        dir_tooltip=ToolTips.apply_dir.value,
        file_label=OpBtn.apply_file.value,
        file_no_status_tooltip=ToolTips.file_no_status.value,
        file_tooltip=ToolTips.apply_file.value,
        initial_label=OpBtn.apply_path.value,
    )
    re_add_path = ApplyReAddButtonData(
        dir_label=OpBtn.re_add_dir.value,
        dir_no_status_tooltip=ToolTips.dir_no_status.value,
        dir_tooltip=ToolTips.re_add_dir.value,
        file_label=OpBtn.re_add_file.value,
        file_no_status_tooltip=ToolTips.file_no_status.value,
        file_tooltip=ToolTips.re_add_file.value,
        initial_label=OpBtn.re_add_path.value,
    )
    forget_path = DestroyForgetButtonData(
        dir_label=OpBtn.forget_dir.value,
        dir_tooltip=ToolTips.forget_dir.value,
        file_label=OpBtn.forget_file.value,
        file_tooltip=ToolTips.forget_file.value,
        initial_label=OpBtn.forget_path.value,
    )
    destroy_path = DestroyForgetButtonData(
        dir_label=OpBtn.destroy_dir.value,
        dir_tooltip=ToolTips.destroy_dir.value,
        file_label=OpBtn.destroy_file.value,
        file_tooltip=ToolTips.destroy_file.value,
        initial_label=OpBtn.destroy_path.value,
    )
    init_new_repo = InitScreenNewRepositoryButtonData()
    init_clone_repo = InitScreenCloneRepositoryButtonData()
    init_exit = InitScreenExitButtonData()
    operate_exit = OperateScreenExitButtonData(
        cancel_label=OpBtn.operate_cancel.value,
        close_label=OpBtn.operate_close.value,
        initial_label=OpBtn.operate_cancel.value,
    )

    # allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def close_label(self) -> str:
        if isinstance(
            self.value, (OperateScreenExitButtonData, InitScreenExitButtonData)
        ):
            return self.value.close_label
        raise AttributeError(f"{self.name} has no close_label")

    @property
    def cancel_label(self) -> str:
        if isinstance(self.value, OperateScreenExitButtonData):
            return self.value.cancel_label
        raise AttributeError(f"{self.name} has no cancel_label")

    @property
    def enabled_tooltip(self) -> str:
        if isinstance(self.value, AddButtonData):
            return self.value.enabled_tooltip
        raise AttributeError(f"{self.name} has no enabled_tooltip")

    @property
    def disabled_tooltip(self) -> str:
        if isinstance(self.value, AddButtonData):
            return self.value.disabled_tooltip
        raise AttributeError(f"{self.name} has no disabled_tooltip")

    @property
    def dir_no_status_tooltip(self) -> str:
        if isinstance(self.value, ApplyReAddButtonData):
            return self.value.dir_no_status_tooltip
        raise AttributeError(f"{self.name} has no dir_no_status_tooltip")

    @property
    def dir_tooltip(self) -> str:
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.dir_tooltip
        raise AttributeError(f"{self.name} has no dir_tooltip")

    @property
    def file_no_status_tooltip(self) -> str:
        if isinstance(self.value, ApplyReAddButtonData):
            return self.value.file_no_status_tooltip
        raise AttributeError(f"{self.name} has no file_no_status_tooltip")

    @property
    def file_tooltip(self) -> str:
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.file_tooltip
        raise AttributeError(f"{self.name} has no file_tooltip")

    @property
    def initial_tooltip(self) -> str:
        return ToolTips.initial

    @property
    def _file_label(self) -> str:
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.file_label
        elif isinstance(self.value, AddButtonData):
            return self.value.initial_label
        raise AttributeError(f"{self.name} has no file_label")

    @property
    def _dir_label(self) -> str:
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.dir_label
        elif isinstance(self.value, AddButtonData):
            return self.value.initial_label
        raise AttributeError(f"{self.name} has no dir_label")

    def label(self, path_type: "PathKind | None" = None) -> str:
        if path_type == "dir":
            return self._dir_label
        elif path_type == "file":
            return self._file_label
        else:
            return self.value.initial_label

    def tooltip(self, path_type: "PathKind | None" = None) -> str:
        if path_type == "dir":
            return self.dir_tooltip
        elif path_type == "file":
            return self.file_tooltip
        else:
            return "Tooltip not yet implomented."

    @classmethod
    def from_label(cls, label: str) -> "OperateBtn":
        for member in cls:
            if getattr(member.value, "file_label", None) == label:
                return member
            elif getattr(member.value, "dir_label", None) == label:
                return member
            elif getattr(member.value, "initial_label", None) == label:
                return member
        raise ValueError(f"{cls.__name__} has no member with label={label!r}")
