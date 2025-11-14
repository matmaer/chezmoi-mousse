from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Pretty

from chezmoi_mousse import ViewName
from chezmoi_mousse.shared import MainSectionLabelText, SectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class CatConfigOutput(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.cat_config_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(MainSectionLabelText.cat_config_output)
        yield ScrollableContainer(
            Pretty("<cat-config>", id=ViewName.pretty_cat_config_view),
            id=self.ids.view_id(view=ViewName.cat_config_view),
        )
