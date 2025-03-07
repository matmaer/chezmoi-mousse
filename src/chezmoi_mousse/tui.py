from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Pretty, Static, TabbedContent

from chezmoi_mousse.common import FLOW, chezmoi, oled_dark_zen
from chezmoi_mousse.operator import ChezmoiDoctor
from chezmoi_mousse.splash import LoadingScreen


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "operations": App.get_default_screen,
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        with TabbedContent(
            "Doctor",
            "Diagram",
            "Chezmoi-Status",
            "Dump-Config",
            "Template-Data",
            "Unmanaged",
            "Cat-Config",
            "Git-Log",
            "Git-Status",
            "Ignored",
            "Managed-Files",
        ):
            yield ChezmoiDoctor()
            yield Static(FLOW, id="diagram")
            yield Pretty(chezmoi.chezmoi_status.py_out)
            yield Pretty(chezmoi.dump_config.py_out)
            yield Pretty(chezmoi.template_data.py_out)
            yield Pretty(chezmoi.unmanaged.py_out)
            yield Pretty(chezmoi.cat_config.py_out)
            yield Pretty(chezmoi.git_log.py_out)
            yield Pretty(chezmoi.git_status.py_out)
            yield Pretty(chezmoi.ignored.py_out)
            yield Pretty(chezmoi.managed.py_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading", self.refresh_app)

    # Screen dismiss from the loading screen, returns something even though,
    # marked as optional in the docs, so adding an underscore
    # to avoid exception that says refresh takes only one argument
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)
