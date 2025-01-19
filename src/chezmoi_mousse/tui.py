"""Contains the Textual App class for the TUI."""

from textual.app import App
from textual.binding import Binding

from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.greeter import GreeterScreen


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    BINDINGS = [
        Binding(
            key="o",
            action="app.switch_mode('operate')",
            description="Operate",
            tooltip="Show the operations screen",
        ),
        Binding(
            key="i",
            action="app.switch_mode('inspect')",
            description="Inspect",
            tooltip="Show the inspect screen",
        ),
    ]
    MODES = {
        "greeter": GreeterScreen,
        "operate": OperationTabs,
        "inspect": InspectTabs,
    }
    DEFAULT_MODE = "greeter"

    # 'check_action' is stolen from Will McGugan's textual demo application:
    # https://github.com/Textualize/textual/blob/f5be1b7aba017b3489824fbcf51b5f8b0820a4ee/src/textual/demo/demo_app.py
    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Disable switching to a mode we are already on."""
        if (
            action == "switch_mode"
            and parameters
            and self.current_mode == parameters[0]
        ):
            return None
        return True
