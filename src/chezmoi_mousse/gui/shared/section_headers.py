from enum import StrEnum
from typing import TYPE_CHECKING

from textual.content import Content
from textual.widgets import Label, RichLog

from chezmoi_mousse import CanvasName, Tcss, ViewName

__all__ = ["InitialHeader", "SectionHeader", "SectionLabel"]

if TYPE_CHECKING:
    from .canvas_ids import CanvasIds


class Strings(StrEnum):
    in_dest_dir = 'This is the destination directory "chezmoi destDir"'
    initial_git_log_msg = (
        'Click a path in the tree to see the output from "chezmoi git log".'
    )


class SectionLabel(Label):

    def __init__(self, label_text: str) -> None:
        super().__init__(label_text, classes=Tcss.section_header.name)

    def on_mount(self) -> None:
        self.add_class(Tcss.section_label.name)


class SectionSubLabel(Label):

    def __init__(self, label_text: str) -> None:
        super().__init__(label_text, classes=Tcss.section_header.name)

    def on_mount(self) -> None:
        self.add_class(Tcss.section_sub_label.name)


class SectionHeader(RichLog):
    def __init__(
        self,
        ids: "CanvasIds",
        view_name: ViewName,
        messages: list[Content],
        initial: bool = False,
    ) -> None:
        self.messages = messages
        if initial:
            self.super_id = ids.initial_header_id(view_name=view_name)
        else:
            self.super_id = ids.section_header_id(view_name=view_name)

        super().__init__(
            id=self.super_id,
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            markup=True,
            classes=Tcss.section_header.name,
        )


class InitialHeader(SectionHeader):
    def __init__(self, ids: "CanvasIds", view_name: ViewName) -> None:
        self.ids = ids
        self.view_name = view_name
        super().__init__(
            ids=ids, view_name=view_name, messages=[], initial=True
        )

    def on_mount(self) -> None:
        self.add_class(Tcss.rich_header.name)
        self.write(Content(Strings.in_dest_dir))
        if (
            self.ids.canvas_name
            in (CanvasName.apply_tab, CanvasName.re_add_tab)
            and self.view_name == ViewName.git_log_view
        ):
            self.write(Content(Strings.initial_git_log_msg))
