import os

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


class DebugUtils:
    @staticmethod
    def print_env_vars():
        for key, value in os.environ.items():
            print(f"{key}: {value}")


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


# logging message, example from Jazzhands:
# @on(MyWidget.EventFoo)
# async def cell_chosen(self, event: MyWidget.EventFoo):
#     self.log.debug(
#         f"event_foo: {event} \n"
#         f"Row, col: {event.row}, {event.column}"    # example attributes in event
#     )
# handle event

# Will
# self.log(self.css)
# Jazz
# self.log(self.css_tree
