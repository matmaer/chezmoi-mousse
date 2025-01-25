from textual.app import App, ComposeResult
from textual.widgets import Footer

from chezmoi_mousse.greeter import LoadingScreen
from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen("loading")
