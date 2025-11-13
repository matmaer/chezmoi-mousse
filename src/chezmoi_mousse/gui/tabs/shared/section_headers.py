from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.content import Content
from textual.widgets import Label, Static

from chezmoi_mousse import Tcss, ViewName

__all__ = ["InitialHeader", "SectionHeader", "SectionLabel", "SectionSubLabel"]

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds


class SectionStrings(StrEnum):
    path_info = "Path Information"
    in_dest_dir = 'This is the destination directory "chezmoi destDir"'
    initial_git_log_msg = (
        'Click a path in the tree to see the output from "chezmoi git log".'
    )
    initial_diff_msg = (
        'Click a path in the tree to see the output from "chezmoi diff".'
    )
    initial_contents_msg = "Click a path in the tree to see the file contents."


class SectionLabel(Label):

    def __init__(self, label_text: str) -> None:
        super().__init__(label_text, classes=Tcss.section_header.name)


class SectionSubLabel(Label):

    def __init__(self, label_text: str) -> None:
        super().__init__(label_text, classes=Tcss.section_header.name)


class SectionHeader(Static):
    def __init__(
        self, ids: "CanvasIds", view_name: ViewName, messages: list[Content]
    ) -> None:
        self.messages = messages
        super().__init__(
            id=ids.section_header_id(view_name=view_name),
            markup=True,
            classes=Tcss.section_header.name,
        )


class InitialHeader(Vertical):
    def __init__(self, ids: "CanvasIds", view_name: ViewName) -> None:
        super().__init__(classes=Tcss.section_header.name)
        self.ids = ids
        self.view_name = view_name
        self.static_id = self.ids.initial_header_id(view_name=self.view_name)
        self.static_qid = self.ids.initial_header_id(
            "#", view_name=self.view_name
        )

    def compose(self) -> ComposeResult:
        yield SectionSubLabel(SectionStrings.path_info)
        yield Static("", id=self.static_id)

    def on_mount(self) -> None:
        static_widget = self.query_one(self.static_qid, Static)
        lines_to_add: list[str] = []
        lines_to_add.append(SectionStrings.in_dest_dir)
        if self.view_name == ViewName.diff_view:
            lines_to_add.append(SectionStrings.initial_diff_msg)
        elif self.view_name == ViewName.contents_view:
            lines_to_add.append(SectionStrings.initial_contents_msg)
        elif self.view_name == ViewName.git_log_view:
            lines_to_add.append(SectionStrings.initial_git_log_msg)
        static_widget.update("\n".join(lines_to_add))
