from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Pretty

from chezmoi_mousse import ViewName

from ._section_headers import MainSectionLabelText, SectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["TemplateDataOutput"]


class TemplateDataOutput(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.template_data_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(MainSectionLabelText.template_data_output)
        yield ScrollableContainer(
            Pretty("<template_data>", id=ViewName.pretty_template_data_view),
            id=self.ids.view_id(view=ViewName.template_data_view),
        )
