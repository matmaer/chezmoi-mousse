from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Label, Pretty

# `textual console`: the -x flag can be used to exclude one or more groups:

# EVENT
# DEBUG
# INFO
# WARNING
# ERROR
# PRINT
# SYSTEM
# LOGGING
# WORKER

# Multiple groups may be excluded, for example:
# textual console -x SYSTEM -x EVENT -x DEBUG -x INFO


class VariablesScreen(ModalScreen):
    DEFAULT_CSS = """
    VariablesScreen {
        #vars {
            border: heavy $accent;
            margin: 2 4;
            scrollbar-gutter: stable;
            Static {
                width: auto;
            }
        }
    }
    """
    BINDINGS = [("escape", "dismiss", "Dismiss")]

    def __init__(self, local_vars: dict, global_vars: dict) -> None:
        super().__init__()
        self.local_vars = local_vars
        self.global_vars = global_vars

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="vars"):
            yield Label("Global Variables", variant="primary")
            yield Pretty(self.global_vars)
            yield Label("Local Variables", variant="primary")
            yield Pretty(self.local_vars)
