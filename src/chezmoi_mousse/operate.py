"""Constructs the operate screen."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent

from chezmoi_mousse.graphic import FLOW_DIAGRAM
from chezmoi_mousse.logslider import LogSlidebar
from chezmoi_mousse.widgets import ChezmoiStatus, ManagedFiles


class OperationTabs(Screen):

    BINDINGS = [
        ("i", "app.push_screen('inspect')", "inspect"),
        ("l", "toggle_sidebar", "command-log"),
    ]

    show_sidebar = reactive(False)

    def log_to_slidebar(self, message: str) -> None:
        self.query_one("#richlog-slidebar").write(message)

    def compose(self) -> ComposeResult:
        yield Header()
        yield LogSlidebar()
        with VerticalScroll():
            with TabbedContent(
                "Chezmoi-Diagram",
                "Managed-Files",
                "Status-Overview",
            ):
                yield Static(FLOW_DIAGRAM, id="diagram")
                yield ManagedFiles()
                yield ChezmoiStatus()
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- o p e r a t e -"
        self.log_to_slidebar("operating")

    def action_toggle_sidebar(self) -> None:
        self.show_sidebar = not self.show_sidebar

    def watch_show_sidebar(self, show_sidebar: bool) -> None:
        # Toggle "visible" class when "show_sidebar" reactive changes.
        self.query_one(LogSlidebar).set_class(show_sidebar, "-visible")