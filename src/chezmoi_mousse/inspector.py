"""Contains the Inspector Screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Pretty,
    TabbedContent,
)

from chezmoi_mousse import chezmoi
from chezmoi_mousse.widgets import ChezmoiDoctor


class InspectTabs(Screen):
    def compose(self) -> ComposeResult:
        with TabbedContent(
            "Doctor",
            "Config-Dump",
            "Template-Data",
            "Config-File",
            "Ignored",
        ):
            yield ChezmoiDoctor()
            yield Pretty(chezmoi.dump_config())
            yield Pretty(chezmoi.data())
            yield Pretty(chezmoi.cat_config())
            yield Pretty(chezmoi.ignored())
        yield Footer()
