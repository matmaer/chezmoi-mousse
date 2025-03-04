# from textual import work
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Header,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse import chezmoi
from chezmoi_mousse.common import FLOW_DIAGRAM, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            # "Chezmoi-Status",
            "Diagram",
            # "Dump-Config",
            "Template-Data",
            "Unmanaged",
            # "Cat-Config",
            # "Doctor",
            "Git-Log",
            # "Git-Status",
            # "Ignored",
            # "Managed-Files",
        ):
            # yield Pretty(getattr(chezmoi, "status").long_command)
            yield Static(FLOW_DIAGRAM, id="diagram")
            # yield Static(getattr(chezmoi, "dump_config").long_command)
            yield Pretty(chezmoi.data.py_out) # pylint: disable=no-member
            yield Pretty(chezmoi.unmanaged.py_out) # pylint: disable=no-member
            # yield ChezmoiDoctor(getattr(chezmoi, "doctor"))
            # yield ChezmoiStatus(self.chezmoi.status.py_out)
            # yield ManagedFiles(getattr(chezmoi, "managed").long_command)
            # yield Pretty(chezmoi.io["cat_config"].py_out)
            # yield Pretty(chezmoi.io["ignored"].long_command)
            yield Pretty(chezmoi.git_log.py_out) # pylint: disable=no-member

        yield Footer()

    def on_mount(self) -> None:

        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading")
