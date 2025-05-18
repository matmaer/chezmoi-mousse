from textual.app import App, ComposeResult
from textual.lazy import Lazy
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Header, TabbedContent

from chezmoi_mousse.mousse import (
    AddTab,
    ApplyTab,
    DiagramTab,
    DoctorTab,
    ReAddTab,
)
from chezmoi_mousse.splash import LoadingScreen


class MainScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent("Add", "Apply", "Re-Add", "Doctor", "Diagram"):
            yield AddTab()
            yield Lazy(ApplyTab())
            yield Lazy(ReAddTab())
            yield Lazy(DoctorTab())
            yield Lazy(DiagramTab())
        yield Footer()


chezmoi_mousse_dark = Theme(
    name="chezmoi-mousse-dark",
    dark=True,
    accent="#F187FB",
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DEDAE1",
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    surface="#101010",  # see also textual/theme.py
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)


class ChezmoiTUI(App):

    CSS_PATH = "gui.tcss"

    SCREENS = {"main": MainScreen, "loading": LoadingScreen}

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen("loading", self.push_main_screen)

    def push_main_screen(self, _) -> None:
        self.push_screen("main")
