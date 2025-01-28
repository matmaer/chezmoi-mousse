from textual.app import App, ComposeResult
from textual.widgets import Footer

from chezmoi_mousse.greeter import LoadingScreen
from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.graphic import oled_deep_zen


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
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        # self.push_screen("inspect")
        self.push_screen("loading")
