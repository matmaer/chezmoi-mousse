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


class SharedLabels(StrEnum):
    cancel = "Cancel"
    close = "Close"
    exit_app = "Exit App"


class SharedToolTips(StrEnum):
    dir_no_status = "The selected directory has no status to operate on."
    file_no_status = "The selected file has no status to operate on."
    initial = "This is the destDir, select a path to operate on."


@dataclass(slots=True)
class ApplyButtonData:
    dir_label = "Apply Dir"
    dir_no_status_tooltip = SharedToolTips.dir_no_status.value
    dir_tooltip = 'Run "chezmoi apply" on the directory.'
    file_label = "Apply File"
    file_no_status_tooltip = SharedToolTips.file_no_status.value
    file_tooltip = 'Run "chezmoi apply" on the file.'
    initial_label = "Apply Path"


@dataclass(slots=True)
class ReAddButtonData:
    dir_label = "Re-Add Dir"
    dir_no_status_tooltip = SharedToolTips.dir_no_status.value
    dir_tooltip = 'Run "chezmoi re-add" on the directory.'
    file_label = "Re-Add File"
    file_no_status_tooltip = SharedToolTips.file_no_status.value
    file_tooltip = 'Run "chezmoi re-add" on the file.'
    initial_label = "Re-Add Path"


@dataclass(slots=True)
class DestroyButtonData:
    dir_label = "Destroy Dir"
    dir_tooltip = 'Run "chezmoi destroy" on the directory. Permanently remove the directory and its files from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!'
    file_label = "Destroy File"
    file_tooltip = 'Run "chezmoi destroy" on the file. Permanently remove the file from disk and chezmoi. MAKE SURE YOU HAVE A BACKUP!'
    initial_label = "Destroy Path"


@dataclass(slots=True)
class ForgetButtonData:
    dir_label = "Forget Dir"
    dir_tooltip = 'Run "chezmoi forget", stop managing the directory.'
    file_label = "Forget File"
    file_tooltip = 'Run "chezmoi forget", stop managing the file.'
    initial_label = "Forget Path"


@dataclass(slots=True)
class AddFileButtonData:
    disabled_tooltip = "Select a file to operate on."
    enabled_tooltip = "Manage the file with chezmoi."
    initial_label = "Add File"


@dataclass(slots=True)
class AddDirButtonData:
    disabled_tooltip = "Select a directory to operate on."
    enabled_tooltip = "Manage the directory with chezmoi."
    initial_label = "Add Dir"


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
    exit_app_label: str = SharedLabels.exit_app.value
    exit_app_tooltip: str = (
        "Ext application. Cannot run the main application without an initialized chezmoi state, init a new repository, or init from a remote repository."
    )
    close_label: str = SharedLabels.close.value
    close_tooltip: str = (
        "Restart the application to load the initialized chezmoi state."
    )
    initial_label: str = exit_app_label  # used by the OperateButton class


@dataclass(slots=True)
class OperateScreenExitButtonData:
    cancel_label: str = SharedLabels.cancel.value
    close_label: str = SharedLabels.close.value
    initial_label: str = SharedLabels.cancel.value


class OperateBtn(Enum):
    add_file = AddFileButtonData()
    add_dir = AddDirButtonData()
    apply_path = ApplyButtonData()
    re_add_path = ReAddButtonData()
    forget_path = ForgetButtonData()
    destroy_path = DestroyButtonData()
    init_new_repo = InitScreenNewRepositoryButtonData()
    init_clone_repo = InitScreenCloneRepositoryButtonData()
    init_exit = InitScreenExitButtonData()
    operate_exit = OperateScreenExitButtonData()

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
        if isinstance(self.value, (AddFileButtonData, AddDirButtonData)):
            return self.value.enabled_tooltip
        raise AttributeError(f"{self.name} has no enabled_tooltip")

    @property
    def disabled_tooltip(self) -> str:
        if isinstance(self.value, (AddFileButtonData, AddDirButtonData)):
            return self.value.disabled_tooltip
        raise AttributeError(f"{self.name} has no disabled_tooltip")

    @property
    def dir_no_status_tooltip(self) -> str:
        if isinstance(self.value, (ApplyButtonData, ReAddButtonData)):
            return self.value.dir_no_status_tooltip
        raise AttributeError(f"{self.name} has no dir_no_status_tooltip")

    @property
    def dir_tooltip(self) -> str:
        if isinstance(
            self.value,
            (
                ApplyButtonData,
                ReAddButtonData,
                DestroyButtonData,
                ForgetButtonData,
            ),
        ):
            return self.value.dir_tooltip
        raise AttributeError(f"{self.name} has no dir_tooltip")

    @property
    def file_no_status_tooltip(self) -> str:
        if isinstance(self.value, (ApplyButtonData, ReAddButtonData)):
            return self.value.file_no_status_tooltip
        raise AttributeError(f"{self.name} has no file_no_status_tooltip")

    @property
    def file_tooltip(self) -> str:
        if isinstance(
            self.value,
            (
                ApplyButtonData,
                ReAddButtonData,
                DestroyButtonData,
                ForgetButtonData,
            ),
        ):
            return self.value.file_tooltip
        raise AttributeError(f"{self.name} has no file_tooltip")

    @property
    def initial_tooltip(self) -> str:
        return SharedToolTips.initial

    @property
    def _file_label(self) -> str:
        if isinstance(
            self.value,
            (
                ApplyButtonData,
                ReAddButtonData,
                DestroyButtonData,
                ForgetButtonData,
            ),
        ):
            return self.value.file_label
        elif isinstance(self.value, AddFileButtonData):
            return self.value.initial_label
        raise AttributeError(f"{self.name} has no file_label")

    @property
    def _dir_label(self) -> str:
        if isinstance(
            self.value,
            (
                ApplyButtonData,
                ReAddButtonData,
                DestroyButtonData,
                ForgetButtonData,
            ),
        ):
            return self.value.dir_label
        elif isinstance(self.value, AddDirButtonData):
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
