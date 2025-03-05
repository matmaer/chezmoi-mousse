from textual.app import App, ComposeResult

from textual.widgets import (
    Footer,
    Header,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import Chezmoi, FLOW, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    chezmoi = Chezmoi()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            "Diagram",
            "Chezmoi-Status",
            "Chezmoi-Status2",
            "Chezmoi-Status3",
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
            yield Pretty(self.chezmoi.status.std_out, id="chezmoi-status")
            yield Pretty(self.app.chezmoi.status.std_out, id="chezmoi-status2")
            yield Pretty(self.app.chezmoi.status.py_out, id="chezmoi-status3")

        yield Footer()

    def store_data(self, io_data: dict) -> None:
        for arg_id, arg_data in io_data.items():
            setattr(self.chezmoi, arg_id, arg_data)

    def on_mount(self) -> None:

        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen(LoadingScreen(), self.store_data)
