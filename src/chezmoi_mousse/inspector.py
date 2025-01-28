"""Contains the Inspector Screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Pretty, TabbedContent

from chezmoi_mousse.commands import ChezmoiCommands
from chezmoi_mousse.widgets import ChezmoiDoctor

chezmoi = ChezmoiCommands()


class InspectTabs(Screen):
    BINDINGS = [
        Binding(
            key="t",
            action="app.push_screen('operate')",
            description="Toggle operate/inspect screen",
        ),
    ]

    def compose(self) -> ComposeResult:
        with TabbedContent(
            "Doctor",
            "Config-Dump",
            "Template-Data",
            "Config-File",
            "Ignored",
        ):
            yield ChezmoiDoctor()
            yield Pretty(chezmoi.dump_config(), classes="horipad")
            yield Pretty(chezmoi.data(), classes="horipad")
            yield Pretty(chezmoi.cat_config(), classes="horipad")
            yield Pretty(chezmoi.ignored(), classes="horipad")
        yield Footer()
