from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Pretty

from chezmoi_mousse import ViewName

from ._section_headers import SectionLabel, SectionLabelText

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["TemplateDataOutput"]


class TemplateDataOutput(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.template_data_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.template_data_output)

    def on_mount(self) -> None:
        self.mount(
            ScrollableContainer(
                Pretty(
                    "<template_data>", id=ViewName.pretty_template_data_view
                )
            )
        )
