from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from chezmoi_mousse import SplashData

__all__ = ["InitScreen"]

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds


class InitScreen(Screen[None]):

    def __init__(
        self, *, ids: "CanvasIds", commands_data: "SplashData"
    ) -> None:
        super().__init__()
        self.commands_data = commands_data

    def compose(self) -> ComposeResult:
        yield Static("Placeholder for chezmoi init screen")
        yield Static("Commands Data:")
        yield Static(f"{dir(self.commands_data)}")
