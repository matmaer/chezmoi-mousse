from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Label, Static

from chezmoi_mousse import ViewName

__all__ = [
    "InitialHeader",
    "SectionLabel",
    "SectionLabelText",
    "SubSectionLabel",
]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


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


class SectionLabel(Label):

    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class SubSectionLabel(Label):
    def __init__(self, label_text: str) -> None:
        super().__init__(label_text)


class InitialHeader(VerticalGroup):
    def __init__(self, ids: "CanvasIds", view_name: ViewName) -> None:
        self.ids = ids
        self.view_name = view_name
        self.initial_header_id = self.ids.initial_header_id(
            view_name=self.view_name
        )

        super().__init__(id=self.initial_header_id)
        self.static_id = f"{self.initial_header_id}_static"
        self.static_qid = f"#{self.static_id}"

    def compose(self) -> ComposeResult:
        yield SubSectionLabel(SectionLabelText.path_info)
        yield Static("", id=self.static_id)

    def on_mount(self) -> None:
        static_widget = self.query_one(self.static_qid, Static)
        lines_to_add: list[str] = []
        lines_to_add.append(SectionLabelText.in_dest_dir)
        if self.view_name == ViewName.diff_view:
            lines_to_add.append(SectionLabelText.initial_diff_msg)
        elif self.view_name == ViewName.contents_view:
            lines_to_add.append(SectionLabelText.initial_contents_msg)
        elif self.view_name == ViewName.git_log_view:
            lines_to_add.append(SectionLabelText.initial_git_log_msg)
        static_widget.update("\n".join(lines_to_add))
