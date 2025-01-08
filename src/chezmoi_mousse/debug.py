"""Debugging aids for the app itself."""

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Pretty, TabbedContent, Footer
from chezmoi_mousse.commands import CommandLog


class DebugTabs(Screen):
    def __init__(self):
        super().__init__()
        self.local_vars = None
        self.global_vars = None

    def compose(self):
        self.global_vars = globals()
        del self.global_vars["__builtins__"]
        with TabbedContent(
            "Command Log",
            "Global Vars",
            "Local Vars",
        ):
            yield CommandLog()
            with VerticalScroll():
                yield Pretty(self.global_vars)
            with VerticalScroll():
                yield Pretty(self.local_vars)
        yield Footer()
