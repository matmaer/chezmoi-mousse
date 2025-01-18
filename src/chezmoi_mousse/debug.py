"""Debugging aids for the app itself."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Pretty, TabbedContent, Footer


class DebugTabs(Screen):
    def __init__(self, local_vars, global_vars):
        super().__init__()
        self.local_vars = local_vars
        self.global_vars = global_vars

    def compose(self) -> ComposeResult:
        del self.global_vars["__builtins__"]
        with TabbedContent(
            "Global-Vars",
            "Local-Vars",
        ):
            yield Pretty(self.global_vars)
            yield Pretty(self.local_vars)
        yield Footer()
