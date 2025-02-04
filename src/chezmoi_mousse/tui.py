from textual.app import App
from textual.binding import Binding

from chezmoi_mousse.graphics import oled_deep_zen
from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.loader import LoadingScreen
from chezmoi_mousse.operator import OperationTabs


class ChezmoiTUI(App):
    BINDINGS = [
        Binding(
            key="i",
            action="app.push_screen('inspect')",
            description="inspect",
            show=False,
        ),
        Binding(
            key="o",
            action="app.push_screen('operate')",
            description="operate",
            show=False,
        ),
        Binding(
            key="r",
            action="app.push_screen('loader')",
            description="loader",
            show=False,
        ),
        Binding(
            key="s",
            action="toggle_sidebar",
            description="slidebar",
            show=False,
        ),
    ]

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        "loader": LoadingScreen,
    }

    def on_mount(self) -> None:
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        self.push_screen("loader")
