from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from chezmoi_mousse import CommandsData

__all__ = ["ChezmoiInit"]


class ChezmoiInit(Screen[None]):

    def __init__(self, *, commands_data: "CommandsData") -> None:
        super().__init__()
        self.commands_data = commands_data

    def compose(self) -> ComposeResult:
        yield Static("Placeholder for chezmoi init screen")
        yield Static("Commands Data:")
        yield Static(f"{dir(self.commands_data)}")
