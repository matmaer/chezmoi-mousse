from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.lazy import Lazy
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Header, TabbedContent, TabPane

from chezmoi_mousse.main_tabs import (
    AddTab,
    ApplyTab,
    DiagramTab,
    DoctorTab,
    ReAddTab,
)
from chezmoi_mousse.splash import LoadingScreen


class MainScreen(Screen):

    BINDINGS = [
        Binding(
            key="W,w",
            action="apply_path",
            description="write-dotfile",
            tooltip="write to dotfiles from your chezmoi repository",
        ),
        Binding(
            key="A,a",
            action="re_add_path",
            description="re-add-chezmoi",
            tooltip="overwrite chezmoi repository with your current dotfiles",
        ),
        Binding(
            key="A,a",
            action="add_path",
            description="chezmoi-add",
            tooltip="add new file to your chezmoi repository",
        ),
        Binding(key="C,c", action="open_config", description="chezmoi-config"),
        Binding(
            key="G,g",
            action="git_log",
            description="show-git-log",
            tooltip="git log from your chezmoi repository",
        ),
        Binding(key="escape", action="dismiss", description="close"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="main_tabbed_content"):
            with TabPane("Apply"):
                yield ApplyTab(id="apply_tab")
            with TabPane("Re-Add"):
                yield Lazy(ReAddTab(id="re_add_tab"))
            with TabPane("Add"):
                yield Lazy(AddTab(id="add_tab"))
            with TabPane("Doctor"):
                yield Lazy(DoctorTab(id="doctor_tab"))
            with TabPane("Diagram"):
                yield Lazy(DiagramTab(id="diagram_tab"))
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
