from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen

from chezmoi_mousse import AppType, CanvasName, FlatBtn, LinkBtn

from .tabs.shared.buttons import FlatButton, FlatLink
from .tabs.shared.canvas_ids import CanvasIds
from .tabs.shared.section_headers import SectionLabel, SectionSubLabel

__all__ = ["ReachOutScreen"]


class Strings(StrEnum):
    top_label = "Unfortunately something went wrong..."
    sub_label = "You found an issue, please reach out and post it on the Github issues page, thank you! This could be fixed quickly, your help is appreciated."


class ReachOutScreen(ModalScreen[None], AppType):

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
                FlatButton(ids=self.ids, button_enum=FlatBtn.close_screen)
            )

    @on(FlatButton.Pressed)
    def close_screen(self, event: FlatButton.Pressed) -> None:
        close_screen_button_id = self.ids.button_id(btn=FlatBtn.close_screen)
        if event.button.id == close_screen_button_id:
            self.app.pop_screen()
