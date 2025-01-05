"""The root chezmoi-mousse module."""

from textual.app import ComposeResult, Widget
from textual.widgets import RichLog
from chezmoi_mousse.operate import ChezmoiCommands


chezmoi = ChezmoiCommands()


class StdOut(Widget):
    def compose(self) -> ComposeResult:
        yield RichLog(
            id="richlog",
            highlight=True,
            wrap=False,
            markup=True,
        )
