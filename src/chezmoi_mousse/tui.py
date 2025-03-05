# from textual import work
from textual.app import App, ComposeResult

# from textual import work
from textual.widgets import (
    Footer,
    Header,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import Chezmoi, FLOW, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    chezmoi = Chezmoi()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            # "Chezmoi-Status",
            "Diagram",
            # "Dump-Config",
            # "Template-Data",
            # "Unmanaged",
            # "Cat-Config",
            # "Doctor",
            # "Git-Log",
            # "Git-Status",
            # "Ignored",
            # "Managed-Files",
        ):
            yield Static(FLOW, id="diagram")

        yield Footer()

    def store_data(self, io_data: dict) -> None:
        for arg_id, arg_data in io_data.items():
            setattr(self.chezmoi, arg_id, arg_data)

    def on_mount(self) -> None:

        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen(LoadingScreen(), self.store_data)
