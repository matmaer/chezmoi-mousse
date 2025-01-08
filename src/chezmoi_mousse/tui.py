"""Contains the Textual App class for the TUI."""

from textual.app import App  # , ComposeResult
from textual.binding import Binding
# from textual.containers import Horizontal, Vertical, VerticalScroll


from chezmoi_mousse.debug import DebugFloater
from chezmoi_mousse.inspector import SettingTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.greeter import GreeterSplash


# class MainMenu(Vertical):
#     def compose(self) -> ComposeResult:
#         yield Button(
#             label="Inspect",
#             id="inspect",
#         )
#         yield Button(
#             label="Operate",
#             id="operate",
#         )
#         yield Button(
#             label="Setting",
#             id="settings",
#         )


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    BINDINGS = [
        # Binding(
        #     key="m",
        #     action="toggle_mainmenu",
        #     description="Main Menu",
        #     key_display="m",
        # ),
        # Binding(
        #     key="s",
        #     action="toggle_richlog",
        #     description="Standard Output",
        #     key_display="s",
        # ),
        # Binding(
        #     key="q",
        #     action="quit",
        #     description="Quit",
        #     key_display="q",
        # ),
        # to be implemented when command palette is customized
        # Binding(
        #     key="h",
        #     action="help",
        #     description="Help",
        #     key_display="h",
        # ),
        Binding(
            "o",
            "app.switch_mode('operate')",
            "Operate",
            tooltip="Show the operations screen",
        ),
        Binding(
            "i",
            "app.switch_mode('inspect')",
            "Inspect",
            tooltip="Show the inspect screen",
        ),
        Binding(
            "d",
            "app.switch_mode('debug')",
            "Debug",
            tooltip="Show the debug screen",
        ),
    ]
    MODES = {
        "greeter": GreeterSplash,
        "operate": OperationTabs,
        "inspect": SettingTabs,
        "debug": DebugFloater,
    }
    DEFAULT_MODE = "greeter"

    # Function "check_action" copied from
    # https://github.com/Textualize/textual/blob/main/src/textual/demo/demo_app.py

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Disable switching to a mode we are already on."""
        if (
            action == "switch_mode"
            and parameters
            and self.current_mode == parameters[0]
        ):
            return None
        return True

    # def action_toggle_mainmenu(self):
    #     self.query_one(MainMenu).toggle_class("-hidden")

    # @on(Button.Pressed, "#inspect")
    # def enter_inspect_mode(self):
    #     self.rlog.write("[cyan]Inspect Mode[/]")
    #     self.rlog.write("[red]Inspect mode is not yet implemented[/]")

    # @on(Button.Pressed, "#operate")
    # def enter_operate_mode(self):
    #     self.rlog.write("[cyan]Operate Mode[/]")
    #     self.rlog.write("[red]Operate mode is not yet implemented[/]")

    # @on(Button.Pressed, "#settings")
    # def enter_config_mode(self):
    #     self.rlog.write("[cyan]Configuration Mode[/]")
    #     self.rlog.write("[red]Configuration mode is not yet implemented[/]")
