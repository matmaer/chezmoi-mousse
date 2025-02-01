"""Constructs the Inspector screen."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Pretty, TabbedContent

from chezmoi_mousse.commands import ChezmoiCommands
from chezmoi_mousse.widgets import ChezmoiDoctor
from chezmoi_mousse.logslider import LogSlidebar
from chezmoi_mousse.loader import ChezmoiOutput


class InspectTabs(Screen):

    BINDINGS = [
        ("o", "app.push_screen('operate')", "operate"),
        ("s", "toggle_sidebar", "slidebar"),
    ]

    chezmoi = ChezmoiCommands()
    chezmoi_output = ChezmoiOutput(chezmoi.data())

    def log_to_slidebar(self, message: str) -> None:
        self.query_one("#richlog-slidebar").write(message)

    def compose(self) -> ComposeResult:
        yield Header(classes="middle")
        yield LogSlidebar()
        with VerticalScroll():
            with TabbedContent(
                "Doctor",
                "Config-Dump",
                # "Template-Data",
                "Config-File",
                "Ignored",
            ):
                yield VerticalScroll(ChezmoiDoctor())
                yield Pretty(self.chezmoi.dump_config(), classes="tabpad")
                # yield Pretty(self.chezmoi_output.data, classes="tabpad")
                yield Pretty(self.chezmoi.cat_config(), classes="tabpad")
                yield Pretty(self.chezmoi.ignored(), classes="tabpad")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- i n s p e c t -"
        self.log_to_slidebar("inspecting")
