from textual.app import App, ComposeResult
from textual.widgets import Footer

# from chezmoi_mousse.greeter import LoadingWidget
from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.custom_theme import oled_deep_zen


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        # "loading": LoadingWidget,
    }

    def compose(self) -> ComposeResult:
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        self.push_screen("inspect")
