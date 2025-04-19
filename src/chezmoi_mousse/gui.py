from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.lazy import Lazy
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Header, Static, TabbedContent

from chezmoi_mousse import FLOW
from chezmoi_mousse.mousse import (
    AddDirTree,
    ApplyTree,
    ChezmoiStatus,
    Doctor,
    ReAddTree,
    SlideBar,
)

# from chezmoi_mousse.main_screen import MainScreen
from chezmoi_mousse.splash_screen import LoadingScreen

theme = Theme(
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


class MainScreen(Screen):

    BINDINGS = [Binding("f", "toggle_slidebar", "Filters")]

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")

        with TabbedContent("Apply", "Re-Add", "Add", "Doctor", "Diagram"):
            yield VerticalScroll(
                Lazy(ChezmoiStatus(apply=True)), ApplyTree(), can_focus=False
            )
            yield VerticalScroll(
                Lazy(ChezmoiStatus(apply=False)), ReAddTree(), can_focus=False
            )
            yield VerticalScroll(AddDirTree(), can_focus=False)
            yield VerticalScroll(Doctor(), id="doctor", can_focus=False)
            yield VerticalScroll(Static(FLOW, id="diagram"))
        yield SlideBar()
        yield Footer()

    def action_toggle_slidebar(self):
        self.screen.query_exactly_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.screen.query_exactly_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {"main": MainScreen, "loading": LoadingScreen}

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(theme)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen("loading", self.push_main_screen)

    def push_main_screen(self, _) -> None:
        self.push_screen("main")
