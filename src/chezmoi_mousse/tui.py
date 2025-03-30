from textual.app import App

from chezmoi_mousse.common import mousse_theme
from chezmoi_mousse.main_screen import MainScreen
from chezmoi_mousse.splash_screen import LoadingScreen


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "main": MainScreen,
        "loading": LoadingScreen,
    }

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(mousse_theme)
        self.theme = "mousse-theme"
        self.push_screen("loading", self.push_main_screen)

    def push_main_screen(self, _) -> None:
        self.push_screen("main")
