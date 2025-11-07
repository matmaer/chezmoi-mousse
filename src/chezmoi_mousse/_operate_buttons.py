from dataclasses import dataclass
from enum import Enum, StrEnum

__all__ = ["OperateBtn"]

INITIAL_TOOLTIP = "This is the destDir, select a path to operate on."


class ChezmoiIoLinks(StrEnum):
    add = "https://www.chezmoi.io/reference/commands/add/"
    apply = "https://www.chezmoi.io/reference/commands/apply/"
    destroy = "https://www.chezmoi.io/reference/commands/destroy/"
    forget = "https://www.chezmoi.io/reference/commands/forget/"
    re_add = "https://www.chezmoi.io/reference/commands/re-add/"


class OperateButtons(StrEnum):
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
    operate_cancel = "Cancel"
    operate_close = "Close"
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
    re_add_dir = 'Run "chezmoi re-add" on the directory.'
    re_add_file = 'Run "chezmoi re-add" on the file.'


@dataclass
class ApplyReAddButtonData:
    dir_label: str
    dir_no_status_tooltip: str
    dir_tooltip: str
    file_label: str
    file_no_status_tooltip: str
    file_tooltip: str
    initial_label: str  # this is the label containing "Path"
    link: str


@dataclass
class DestroyForgetButtonData:
    # We don't need status tooltips here
    dir_label: str
    dir_tooltip: str
    file_label: str
    file_tooltip: str
    initial_label: str  # this is the label containing "Path"
    link: str


@dataclass
class AddButtonData:
    # We don't need status tooltips here
    disabled_tooltip: str
    enabled_tooltip: str
    initial_label: str
    link: str


@dataclass
class ExitButtonData:
    initial_label: str
    close_label: str


class OperateBtn(Enum):
    add_file = AddButtonData(
        disabled_tooltip=ToolTips.add_file_disabled.value,
        enabled_tooltip=ToolTips.add_file.value,
        initial_label=OperateButtons.add_file.value,
        link=ChezmoiIoLinks.add.value,
    )
    add_dir = AddButtonData(
        disabled_tooltip=ToolTips.add_dir_disabled.value,
        enabled_tooltip=ToolTips.add_dir.value,
        initial_label=OperateButtons.add_dir.value,
        link=ChezmoiIoLinks.add.value,
    )
    apply_path = ApplyReAddButtonData(
        dir_label=OperateButtons.apply_dir.value,
        dir_no_status_tooltip=ToolTips.dir_no_status.value,
        dir_tooltip=ToolTips.apply_dir.value,
        file_label=OperateButtons.apply_file.value,
        file_no_status_tooltip=ToolTips.file_no_status.value,
        file_tooltip=ToolTips.apply_file.value,
        initial_label=OperateButtons.apply_path.value,
        link=ChezmoiIoLinks.apply.value,
    )
    re_add_path = ApplyReAddButtonData(
        dir_label=OperateButtons.re_add_dir.value,
        dir_no_status_tooltip=ToolTips.dir_no_status.value,
        dir_tooltip=ToolTips.re_add_dir.value,
        file_label=OperateButtons.re_add_file.value,
        file_no_status_tooltip=ToolTips.file_no_status.value,
        file_tooltip=ToolTips.re_add_file.value,
        initial_label=OperateButtons.re_add_path.value,
        link=ChezmoiIoLinks.re_add.value,
    )
    forget_path = DestroyForgetButtonData(
        dir_label=OperateButtons.forget_dir.value,
        dir_tooltip=ToolTips.forget_dir.value,
        file_label=OperateButtons.forget_file.value,
        file_tooltip=ToolTips.forget_file.value,
        initial_label=OperateButtons.forget_path.value,
        link=ChezmoiIoLinks.forget.value,
    )
    destroy_path = DestroyForgetButtonData(
        dir_label=OperateButtons.destroy_dir.value,
        dir_tooltip=ToolTips.destroy_dir.value,
        file_label=OperateButtons.destroy_file.value,
        file_tooltip=ToolTips.destroy_file.value,
        initial_label=OperateButtons.destroy_path.value,
        link=ChezmoiIoLinks.destroy.value,
    )
    exit_button = ExitButtonData(
        initial_label=OperateButtons.operate_cancel.value,
        close_label=OperateButtons.operate_close.value,
    )

    # allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

    @property
    def close_button_label(self) -> str:
        if isinstance(self.value, ExitButtonData):
            return self.value.close_label
        raise AttributeError(f"{self.name} has no close_button_label")

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
    def dir_label(self) -> str:
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.dir_label
        raise AttributeError(f"{self.name} has no dir_label")

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
    def file_label(self) -> str:
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.file_label
        raise AttributeError(f"{self.name} has no file_label")

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
    def initial_label(self) -> str:
        return self.value.initial_label

    @property
    def initial_tooltip(self) -> str:
        return INITIAL_TOOLTIP

    @property
    def link_url(self) -> str:
        if isinstance(
            self.value,
            (AddButtonData, ApplyReAddButtonData, DestroyForgetButtonData),
        ):
            return self.value.link
        raise AttributeError(f"{self.name} has no link")

    @property
    def link_text(self) -> str:
        if isinstance(
            self.value,
            (AddButtonData, ApplyReAddButtonData, DestroyForgetButtonData),
        ):
            return self.value.link.replace("https://www.", "").rstrip("/")
        raise AttributeError(f"{self.name} has no link")

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
