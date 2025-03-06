from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Pretty, Static, TabbedContent

from chezmoi_mousse.common import FLOW, chezmoi, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "operations": App.get_default_screen,
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            "Chezmoi-Object",
            "Status-Stdout",
            "Status-Pyout",
            # "Dump-Config",
            # "Template-Data",
            # "Unmanaged",
            # "Cat-Config",
            # "Doctor",
            # "Git-Log",
            # "Git-Status",
            # "Ignored",
            # "Managed-Files",
            "Diagram",
        ):
            yield Pretty(
                {
                    "chezmoi": f"{chezmoi}",
                    "chezmoi.status": f"{chezmoi.status}",
                }
            )
            yield Pretty(chezmoi.status.std_out)
            yield Pretty(chezmoi.status.py_out)
            yield Static(FLOW, id="diagram")

        yield Footer()


    def on_mount(self) -> None:

        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading")
