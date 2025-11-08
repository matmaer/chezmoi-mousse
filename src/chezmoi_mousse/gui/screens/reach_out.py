from enum import StrEnum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen

from chezmoi_mousse import CanvasName, FlatBtn, LinkBtn
from chezmoi_mousse.gui.shared.canvas_ids import CanvasIds

from ..shared.buttons import FlatButton, FlatLink
from ..shared.section_headers import SectionLabel, SectionSubLabel


class Strings(StrEnum):
    top_label = "Unfortunately something went wrong..."
    sub_label = "You found an issue, please reach out and post it on the Github issues page, thank you! This could be fixed quickly, your help is appreciated."


class ReachOutScreen(ModalScreen[None]):

    def __init__(self) -> None:
        self.ids = CanvasIds(canvas_name=CanvasName.reach_out_screen)
        super().__init__()

    def compose(self) -> ComposeResult:
        yield SectionLabel(Strings.top_label)
        yield SectionSubLabel(Strings.sub_label)
        with Horizontal():
            yield Vertical(
                FlatLink(ids=self.ids, link_enum=LinkBtn.github_issues)
            )
            yield Vertical(
                FlatButton(ids=self.ids, button_enum=FlatBtn.exit_app)
            )
