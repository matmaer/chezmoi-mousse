"""Constructs the Inspector screen."""

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Pretty, TabbedContent

from chezmoi_mousse.commands import ChezmoiCommands
from chezmoi_mousse.widgets import ChezmoiDoctor
from chezmoi_mousse.logslider import LogSlidebar
from chezmoi_mousse.loader import ChezmoiOutput


class InspectTabs(Screen):

    BINDINGS = [
        ("o", "app.push_screen('operate')", "operate"),
    ]

    show_sidebar = reactive(False)

    chezmoi = ChezmoiCommands()
    chezmoi_output = ChezmoiOutput(chezmoi.data())

    def compose(self) -> ComposeResult:
        yield Header(classes="middle")
        yield LogSlidebar()
        with Vertical():
            with TabbedContent(
                "Doctor",
                "Config-Dump",
                # "Template-Data",
                "Config-File",
                "Ignored",
            ):
                yield VerticalScroll(ChezmoiDoctor())
                yield VerticalScroll(Pretty(self.chezmoi.dump_config()))
                # yield Pretty(self.chezmoi_output.data)
                yield VerticalScroll(Pretty(self.chezmoi.cat_config()))
                yield VerticalScroll(Pretty(self.chezmoi.ignored()))
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- i n s p e c t -"
