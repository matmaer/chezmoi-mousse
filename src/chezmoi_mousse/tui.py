from textual.app import App

from chezmoi_mousse.graphics import oled_deep_zen
# from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.loader import LoadingScreen
from chezmoi_mousse.operator import OperationTabs


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "operate": OperationTabs,
        # "inspect": InspectTabs,
        "loader": LoadingScreen,
    }

    def on_mount(self) -> None:
        self.register_theme(oled_deep_zen)
        self.theme = "oled-deep-zen"
        self.push_screen("loader")
