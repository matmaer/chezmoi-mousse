from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Static

from chezmoi_mousse import ViewName

from ._section_headers import SectionLabel, SectionLabelText

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["CatConfigOutput"]


class CatConfigOutput(Vertical):
    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(id=self.ids.view_id(view=ViewName.cat_config_view))

    def compose(self) -> ComposeResult:
        yield SectionLabel(SectionLabelText.cat_config_output)

    def on_mount(self) -> None:
        self.mount(
            ScrollableContainer(
                Static("<cat-config>", id=ViewName.cat_config_view)
            )
        )
