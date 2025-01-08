"""Contains the Textual App class for the TUI."""

from textual.app import App  # , ComposeResult
from textual.binding import Binding
# from textual.containers import Horizontal, Vertical, VerticalScroll


from chezmoi_mousse.debug import DebugScreen
from chezmoi_mousse.inspect import InspectScreens
from chezmoi_mousse.operate import OperateScreens


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
        # to be implemented when modal/screen/layouts are implemented
        # Binding(
        #     key="escape",
        #     action="app.pop_screen",
        #     description="Go Back",
        #     key_display="esc",
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
    CSS_PATH = "tui.tcss"
    MODES = {
        "operate": OperateScreens,
        "inspect": InspectScreens,
        "debug": DebugScreen,
    }
    DEFAULT_MODE = "operate"

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
