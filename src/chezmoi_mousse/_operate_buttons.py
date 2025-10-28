from dataclasses import dataclass
from enum import Enum, StrEnum

__all__ = ["OperateBtn"]

INITIAL_TOOLTIP = "This is the destDir, select a path to operate on."


class ToolTips(StrEnum):
    add_dir = "Manage this directory with chezmoi."
    add_dir_disabled = "Select a directory to operate on."
    add_file = "Manage this file with chezmoi."
    add_file_disabled = "Select a file to operate on."
    apply_dir = 'Run "chezmoi apply" on this directory.'
    apply_file = 'Run "chezmoi apply" on this file.'
    destroy_dir = "MAKE SURE YOU HAVE A BACKUP!\nPermanently remove this directory and its files from disk and chezmoi."
    destroy_file = "MAKE SURE YOU HAVE A BACKUP!\nPermanently remove this file from disk and chezmoi."
    dir_no_status = "The selected directory has no status to operate on."
    file_no_status = "The selected file has no status to operate on."
    forget_dir = "Stop managing this directory."
    forget_file = "Stop managing this file."
    re_add_dir = "Re-add this directory its files to chezmoi."
    re_add_file = "Re-add this file to chezmoi."


class NameLabels(StrEnum):
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


@dataclass
class ApplyReAddButtonData:
    dir_label: str
    dir_no_status_tooltip: str
    dir_tooltip: str
    file_label: str
    file_no_status_tooltip: str
    file_tooltip: str
    initial_label: str  # this is the label containing "Path"
    initial_tooltip: str = INITIAL_TOOLTIP


@dataclass
class DestroyForgetButtonData:
    # We don't need status tooltips here
    dir_label: str
    dir_tooltip: str
    file_label: str
    file_tooltip: str
    initial_label: str  # this is the label containing "Path"
    initial_tooltip: str = INITIAL_TOOLTIP


@dataclass
class AddButtonData:
    # We don't need status tooltips here
    disabled_tooltip: str
    enabled_tooltip: str
    label: str
    initial_tooltip: str = INITIAL_TOOLTIP


class OperateBtn(Enum):
    add_file = AddButtonData(
        disabled_tooltip=ToolTips.add_file_disabled.value,
        enabled_tooltip=ToolTips.add_file.value,
        label=NameLabels.add_file.value,
    )
    add_dir = AddButtonData(
        disabled_tooltip=ToolTips.add_dir_disabled.value,
        enabled_tooltip=ToolTips.add_dir.value,
        label=NameLabels.add_dir.value,
    )
    apply_path = ApplyReAddButtonData(
        dir_label=NameLabels.apply_dir.value,
        dir_no_status_tooltip=ToolTips.dir_no_status.value,
        dir_tooltip=ToolTips.apply_dir.value,
        file_label=NameLabels.apply_file.value,
        file_no_status_tooltip=ToolTips.file_no_status.value,
        file_tooltip=ToolTips.apply_file.value,
        initial_label=NameLabels.apply_path.value,
    )
    re_add_path = ApplyReAddButtonData(
        dir_label=NameLabels.re_add_dir.value,
        dir_no_status_tooltip=ToolTips.dir_no_status.value,
        dir_tooltip=ToolTips.re_add_dir.value,
        file_label=NameLabels.re_add_file.value,
        file_no_status_tooltip=ToolTips.file_no_status.value,
        file_tooltip=ToolTips.re_add_file.value,
        initial_label=NameLabels.re_add_path.value,
    )
    forget_path = DestroyForgetButtonData(
        dir_label=NameLabels.forget_dir.value,
        dir_tooltip=ToolTips.forget_dir.value,
        file_label=NameLabels.forget_file.value,
        file_tooltip=ToolTips.forget_file.value,
        initial_label=NameLabels.forget_path.value,
    )
    destroy_path = DestroyForgetButtonData(
        dir_label=NameLabels.destroy_dir.value,
        dir_tooltip=ToolTips.destroy_dir.value,
        file_label=NameLabels.destroy_file.value,
        file_tooltip=ToolTips.destroy_file.value,
        initial_label=NameLabels.destroy_path.value,
    )

    # allow access to dataclass attributes directly from the Enum member,
    # without needing to go through the value attribute

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
    def label(self) -> str:
        if isinstance(self.value, AddButtonData):
            return self.value.label
        raise AttributeError(f"{self.name} has no label")

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
        if isinstance(
            self.value, (ApplyReAddButtonData, DestroyForgetButtonData)
        ):
            return self.value.initial_label
        raise AttributeError(f"{self.name} has no initial_label")

    @classmethod
    def from_label(cls, label: str) -> "OperateBtn":
        for member in cls:
            if getattr(member.value, "file_label", None) == label:
                return member
            elif getattr(member.value, "dir_label", None) == label:
                return member
            elif getattr(member.value, "label", None) == label:
                return member
        raise ValueError(f"{cls.__name__} has no member with label={label!r}")
