"""Contains the Textual App class for the TUI."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.greeter import GreeterScreen


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    SCREENS = {
        "greeter": GreeterScreen,
        "operate": OperationTabs,
        "inspect": InspectTabs,
    }
    BINDINGS = [
        Binding(
            key="o",
            action="app.push_screen('operate')",
            description="Operate",
            tooltip="Show the operations screen",
        ),
        Binding(
            key="i",
            action="app.push_screen('inspect')",
            description="Inspect",
            tooltip="Show the inspect screen",
        ),
    ]

    def compose(self) -> ComposeResult:
        yield Footer()
