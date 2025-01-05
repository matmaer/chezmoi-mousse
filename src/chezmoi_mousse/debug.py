"""Debugging aids for the app itself."""

# to be implemented when modal/screen/layouts are implemented

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Pretty, TabbedContent


class DebugTabs(Screen):
    def __init__(self, app_theme_vars: dict, local_vars: dict, global_vars: dict):
        super().__init__()
        self.app_theme_vars = app_theme_vars
        self.local_vars = local_vars
        self.global_vars = global_vars
        # delete python bulitins as we're debugging Textual, not Python
        del self.global_vars["__builtins__"]

    def compose(self):
        with TabbedContent(
            "Globals",
            "Locals",
            "Theme Variables",
        ):
            with VerticalScroll():
                yield Pretty(self.global_vars)
            with VerticalScroll():
                yield Pretty(self.local_vars)
            with VerticalScroll():
                yield Pretty(self.app_theme_vars)
