"""Constructs the operate screen."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent

from chezmoi_mousse.graphic import FLOW_DIAGRAM
from chezmoi_mousse.widgets import ChezmoiStatus, ManagedFiles


class OperationTabs(Screen):

    def compose(self) -> ComposeResult:
        yield Header()
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
