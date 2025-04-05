from textual.app import App
from textual.binding import Binding
from textual.theme import Theme

from chezmoi_mousse.main_screen import MainScreen
from chezmoi_mousse.splash_screen import LoadingScreen


class ChezmoiTUI(App):

    BINDINGS = [
        Binding("escape", "blur", "Unfocus any focused widget", show=False)
    ]

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "main": MainScreen,
        "loading": LoadingScreen,
    }

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(theme)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen("loading", self.push_main_screen)

    def push_main_screen(self, _) -> None:
        self.push_screen("main")


theme = Theme(
    name="chezmoi-mousse-dark",
    dark=True,
    accent="#F187FB",
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DEDAE1",
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)
