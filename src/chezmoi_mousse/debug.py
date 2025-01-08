"""Debugging aids for the app itself."""

# to be implemented when modal/screen/layouts are implemented

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Pretty, TabbedContent, Footer


# class DebugTabs(Screen):
#     def __init__(self, app_theme_vars: dict, local_vars: dict, global_vars: dict):
#         super().__init__()
#         self.app_theme_vars = app_theme_vars
#         self.local_vars = local_vars
#         self.global_vars = global_vars
class DebugScreen(Screen):
    def __init__(self):
        super().__init__()
        self.local_vars = None
        self.global_vars = None
        # delete python bulitins as we're debugging Textual, not Python

    def compose(self):
        self.global_vars = globals()
        del self.global_vars["__builtins__"]

        with TabbedContent(
            "Globals",
            "Locals",
            # "Theme Variables",
        ):
            with VerticalScroll():
                yield Pretty(self.global_vars)
            with VerticalScroll():
                yield Pretty(self.local_vars)
            # with VerticalScroll():
            #     yield Pretty(self.app_theme_vars)
        yield Footer()
