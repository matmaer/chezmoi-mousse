# from textual import work
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Header,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import FLOW_DIAGRAM, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen, chezmoi


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            "Unmanaged",
            "Diagram",
            # "Doctor",
            "Dump-Config",
            # "Chezmoi-Status",
            # "Managed-Files",
            # "Template-Data",
            # "Cat-Config",
            # "Git-Log",
            # "Ignored",
            # "Git-Status",
        ):
            yield Pretty(getattr(chezmoi, "unmanaged").std_out)
            yield Static(FLOW_DIAGRAM, id="diagram")
            # yield ChezmoiDoctor(self.chezmoi.doctor.py_out)
            yield Static(getattr(chezmoi, "dump_config").std_out)
            # yield ChezmoiStatus(self.chezmoi.status.py_out)
            # yield ManagedFiles(self.chezmoi.managed.py_out)
            # yield Pretty(chezmoi.io["data"].py_out)
            # yield Pretty(chezmoi.io["cat_config"].py_out)
            # yield Pretty(chezmoi.io["ignored"].py_out)
            # yield Pretty(chezmoi.io["status"].py_out)

        yield Footer()

    def on_mount(self) -> None:

        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading")
