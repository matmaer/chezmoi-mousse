from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.lazy import Lazy
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from chezmoi_mousse.components import cmd_log
from chezmoi_mousse.main_tabs import AddTab, ApplyTab, DoctorTab, ReAddTab
from chezmoi_mousse.splash import LoadingScreen
from chezmoi_mousse import BURGER, FLOW


class MainScreen(Screen):

    def __init__(self, command_log: list[str]) -> None:
        super().__init__()
        self.command_log = command_log

    def compose(self) -> ComposeResult:
        yield Header(icon=BURGER)
        with TabbedContent():
            with TabPane("Apply", id="apply_tab_pane"):
                yield ApplyTab(id="apply_tab")
            with TabPane("Re-Add", id="re_add_tab_pane"):
                yield Lazy(ReAddTab(id="re_add_tab"))
            with TabPane("Add", id="add_tab_pane"):
                yield Lazy(AddTab(id="add_tab"))
            with TabPane("Doctor", id="doctor_tab_pane"):
                yield Lazy(DoctorTab(id="doctor_tab"))
            with TabPane("Diagram", id="diagram_tab_pane"):
                yield ScrollableContainer(Static(FLOW, id="flow_diagram"))
            with TabPane("Log", id="rich_log_tab_pane"):
                yield cmd_log
        yield Footer()

    def on_mount(self) -> None:
        for cmd in self.command_log:
            cmd_log.add(cmd)


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

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen(LoadingScreen(), self.push_main_screen)

    def push_main_screen(self, command_log) -> None:
        self.push_screen(MainScreen(command_log))
