from enum import StrEnum

from textual.widgets import Label

__all__ = [
    "FlatSectionLabel",
    "MainSectionLabel",
    "SectionLabelText",
    "SubSectionLabel",
]


class SectionLabelText(StrEnum):
    cat_config_output = '"chezmoi cat-config" output'
    doctor_output = '"chezmoi doctor" output'
    ignored_output = '"chezmoi ignored" output'
    operate_context = "Operate Context"
    operate_output = "Operate Command Output"
    password_managers = "Password Manager Information"
    path_info = "Path Information"
    template_data_output = '"chezmoi data" output'


class FlatSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class MainSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class SubSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)
