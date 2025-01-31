from textual.app import App
from textual.binding import Binding

from chezmoi_mousse.loader import LoadingScreen
from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.graphic import oled_deep_zen


class ChezmoiTUI(App):
    BINDINGS = [
        Binding(
            key="i",
            action="app.push_screen('inspect')",
            description="inspect",
        ),
        Binding(
            key="o",
            action="app.push_screen('operate')",
            description="operate",
        ),
        Binding(
            key="r",
            action="app.push_screen('loader')",
            description="loader",
        ),
    ]
    CSS_PATH = "tui.tcss"
    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        "loader": LoadingScreen,
    }

    # def compose(self) -> ComposeResult:
    #     yield OperationTabs()
    #     yield InspectTabs()
    #     yield LoadingScreen()

    def on_mount(self) -> None:
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        # self.push_screen("inspect")
        self.push_screen("loader")
