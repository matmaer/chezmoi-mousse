from enum import StrEnum

from textual.widgets import Label

__all__ = [
    "FlatSectionLabel",
    "SectionLabel",
    "SectionLabelText",
    "SubSectionLabel",
]


class SectionLabelText(StrEnum):
    cat_config_output = '"chezmoi cat-config" output'
    doctor_output = '"chezmoi doctor" output'
    ignored_output = '"chezmoi ignored" output'
    in_dest_dir = 'This is the destination directory "chezmoi destDir"'
    initial_contents_msg = "Click a path in the tree to see the file contents."
    initial_diff_msg = (
        'Click a path in the tree to see the output from "chezmoi diff".'
    )
    initial_git_log_msg = (
        'Click a path in the tree to see the output from "chezmoi git log".'
    )
    operate_context = "Operate Context"
    operate_output = "Operate Command Output"
    password_managers = "Password Manager Information"
    path_info = "Path Information"
    template_data_output = '"chezmoi data" output'


class FlatSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class SectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class SubSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)
