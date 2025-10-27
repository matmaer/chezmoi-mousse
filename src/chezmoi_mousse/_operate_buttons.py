from dataclasses import dataclass
from enum import Enum, StrEnum

__all__ = ["OperateBtn"]


class OperateButtonNameLabel(StrEnum):
    add_dir = "Add Dir"
    add_file = "Add File"
    apply_dir = "Apply Dir"
    apply_file = "Apply File"
    clone_chezmoi_repo = "Clone Repo"
    close_operate_results = "Close Operate Results"
    destroy_dir = "Destroy Dir"
    destroy_file = "Destroy File"
    forget_dir = "Forget Dir"
    forget_file = "Forget File"
    init_new_repo = "Initialize"
    operate_dismiss = "Cancel"
    re_add_dir = "Re-Add Dir"
    re_add_file = "Re-Add File"


@dataclass(frozen=True)
class OperateButtonTooltip:
    select_file: str = "Select a file to operate on."
    select_dir: str = "Select a directory to operate on."
    file_without_status: str = "The selected file has no status to operate on."
    dir_without_status: str = (
        "The selected directory has no status to operate on."
    )


@dataclass(frozen=True)
class OperateButtonData:
    btn_name: str
    label: str
    tooltip: OperateButtonTooltip = OperateButtonTooltip()


class OperateBtn(Enum):
    add_dir = OperateButtonData(
        btn_name=OperateButtonNameLabel.add_dir.name,
        label=OperateButtonNameLabel.add_dir.value,
    )
    add_file = OperateButtonData(
        btn_name=OperateButtonNameLabel.add_file.name,
        label=OperateButtonNameLabel.add_file.value,
    )
    apply_dir = OperateButtonData(
        btn_name=OperateButtonNameLabel.apply_dir.name,
        label=OperateButtonNameLabel.apply_dir.value,
    )
    apply_file = OperateButtonData(
        btn_name=OperateButtonNameLabel.apply_file.name,
        label=OperateButtonNameLabel.apply_file.value,
    )
    clone_chezmoi_repo = OperateButtonData(
        btn_name=OperateButtonNameLabel.clone_chezmoi_repo.name,
        label=OperateButtonNameLabel.clone_chezmoi_repo.value,
    )
    close_operate_results = OperateButtonData(
        btn_name=OperateButtonNameLabel.close_operate_results.name,
        label=OperateButtonNameLabel.close_operate_results.value,
    )
    destroy_dir = OperateButtonData(
        btn_name=OperateButtonNameLabel.destroy_dir.name,
        label=OperateButtonNameLabel.destroy_dir.value,
    )
    destroy_file = OperateButtonData(
        btn_name=OperateButtonNameLabel.destroy_file.name,
        label=OperateButtonNameLabel.destroy_file.value,
    )
    forget_dir = OperateButtonData(
        btn_name=OperateButtonNameLabel.forget_dir.name,
        label=OperateButtonNameLabel.forget_dir.value,
    )
    forget_file = OperateButtonData(
        btn_name=OperateButtonNameLabel.forget_file.name,
        label=OperateButtonNameLabel.forget_file.value,
    )
    init_new_repo = OperateButtonData(
        btn_name=OperateButtonNameLabel.init_new_repo.name,
        label=OperateButtonNameLabel.init_new_repo.value,
    )
    operate_dismiss = OperateButtonData(
        btn_name=OperateButtonNameLabel.operate_dismiss.name,
        label=OperateButtonNameLabel.operate_dismiss.value,
    )
    re_add_dir = OperateButtonData(
        btn_name=OperateButtonNameLabel.re_add_dir.name,
        label=OperateButtonNameLabel.re_add_dir.value,
    )
    re_add_file = OperateButtonData(
        btn_name=OperateButtonNameLabel.re_add_file.name,
        label=OperateButtonNameLabel.re_add_file.value,
    )

    @property
    def tooltip(self) -> OperateButtonTooltip:
        return self.value.tooltip

    @classmethod
    def from_label(cls, label: str) -> "OperateBtn":
        for member in cls:
            if getattr(member.value, "label", None) == label:
                return member
        raise ValueError(f"{cls.__name__} has no member with label={label!r}")
