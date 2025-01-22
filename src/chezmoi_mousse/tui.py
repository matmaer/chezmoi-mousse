# from asyncio import sleep

# from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from chezmoi_mousse.inspector import InspectTabs
from chezmoi_mousse.operate import OperationTabs
from chezmoi_mousse.greeter import LoadingScreen


class ChezmoiTUI(App):
    CSS_PATH = "tui.tcss"
    SCREENS = {
        "operate": OperationTabs,
        "inspect": InspectTabs,
        "loading": LoadingScreen,
    }
    BINDINGS = [
        Binding(
            key="o",
            action="app.push_screen('operate')",
            description="Operate",
            tooltip="Show the operations screen",
        ),
        Binding(
            key="i",
            action="app.push_screen('inspect')",
            description="Inspect",
            tooltip="Inspect chezmoi setup",
        ),
        # TODO
        # Binding(
        #     key="t",
        #     action="app.toggle_class('show-log')",
        #     description="Show Log",  # text should change to hide with reactive
        #     tooltip="Toggle the log panel.",
        # ),
    ]

    def compose(self) -> ComposeResult:
        yield Footer()

    # TODO: use as loading screen for first run
    # @work
    # async def on_mount(self) -> None:
    #     self.push_screen("loading")
    #     await sleep(3)
    #     self.switch_screen("operate")


if __name__ == "__main__":
    app = ChezmoiTUI()
    app.run()
