"""Constructs the Inspector screen."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Pretty, TabbedContent

from chezmoi_mousse.commands import ChezmoiCommands
from chezmoi_mousse.widgets import ChezmoiDoctor
from chezmoi_mousse.logslider import LogSlidebar
from chezmoi_mousse.loader import ChezmoiOutput


class InspectTabs(Screen):

    BINDINGS = [
        ("o", "app.push_screen('operate')", "operate"),
        ("l", "toggle_sidebar", "command-log"),
    ]

    show_sidebar = reactive(False)

    chezmoi = ChezmoiCommands()
    chezmoi_output = ChezmoiOutput(chezmoi.data())

    def log_to_slidebar(self, message: str) -> None:
        self.query_one("#richlog-slidebar").write(message)

    def compose(self) -> ComposeResult:
        yield Header(classes="middle")
        yield LogSlidebar()
        with VerticalScroll():
            with TabbedContent(
                "Doctor",
                "Config-Dump",
                # "Template-Data",
                "Config-File",
                "Ignored",
            ):
                yield VerticalScroll(ChezmoiDoctor())
                yield Pretty(self.chezmoi.dump_config(), classes="tabpad")
                # yield Pretty(self.chezmoi_output.data, classes="tabpad")
                yield Pretty(self.chezmoi.cat_config(), classes="tabpad")
                yield Pretty(self.chezmoi.ignored(), classes="tabpad")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- i n s p e c t -"
        self.log_to_slidebar("inspecting")

    def action_toggle_sidebar(self) -> None:
        self.show_sidebar = not self.show_sidebar

    def watch_show_sidebar(self, show_sidebar: bool) -> None:
        # Toggle "visible" class when "show_sidebar" reactive changes.
        self.query_one(LogSlidebar).set_class(show_sidebar, "-visible")