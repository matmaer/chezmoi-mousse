from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class ChezmoiInit(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Static("Placeholder for chezmoi init screen")
