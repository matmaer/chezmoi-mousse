from textual.content import Content
from textual.widgets import Label, RichLog

from chezmoi_mousse import Tcss

__all__ = ["SectionHeader", "SectionLabel"]


class SectionLabel(Label):

    def __init__(self, label_text: str) -> None:
        super().__init__(label_text, classes=Tcss.section_header.name)


class SectionHeader(RichLog):
    def __init__(self, *, messages: list[Content]) -> None:
        self.messages = messages

        super().__init__(
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            classes=Tcss.border_title_top.name,
            markup=True,
        )
