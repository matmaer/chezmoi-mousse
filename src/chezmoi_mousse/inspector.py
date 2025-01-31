"""Constructs the Inspector screen."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Pretty, TabbedContent

from chezmoi_mousse.commands import ChezmoiCommands
from chezmoi_mousse.widgets import ChezmoiDoctor
from chezmoi_mousse.loader import ChezmoiOutput

chezmoi = ChezmoiCommands()
chezmoi_output = ChezmoiOutput(chezmoi.data())

class InspectTabs(Screen):

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with TabbedContent(
                "Doctor",
                "Config-Dump",
                "Template-Data",
                "Config-File",
                "Ignored",
            ):
                yield VerticalScroll(ChezmoiDoctor())
                yield Pretty(chezmoi.dump_config(), classes="tabpad")
                yield Pretty(chezmoi_output.data, classes="tabpad")
                # yield Pretty("test", classes="tabpad")
                yield Pretty(chezmoi.cat_config(), classes="tabpad")
                yield Pretty(chezmoi.ignored(), classes="tabpad")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- i n s p e c t -"
