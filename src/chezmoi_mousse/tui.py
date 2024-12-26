import subprocess

from textual import on
from textual.app import App, ComposeResult, Widget
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, RichLog, Static

from .diagrams import VISUAL_DIAGRAM


class ButtonSidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Button(
            label="Config",
            id="chezmoi_config",
        )
        yield Button(
            label="Status",
            id="chezmoi_status",
        )
        yield Button(
            label="Managed",
            id="chezmoi_managed",
            tooltip="List the managed files in the home directory",
        )
        yield Button(
            label="Clear Output",
            id="clear_richlog",
        )


class RichLogSidebar(Widget):
    def compose(self) -> ComposeResult:
        yield RichLog(
            id="richlog",
            highlight=True,
            wrap=False,
            markup=True,
        )


class CenterContent(Vertical):
    def compose(self) -> ComposeResult:
        yield Static(VISUAL_DIAGRAM)


class ChezmoiTUI(App):
    BINDINGS = [
        ("l", "toggle_buttonsidebar", "Toggle Left Panel"),
        ("r", "toggle_richlogsidebar", "Toggle Right Panel"),
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "tui.tcss"
    show_richlog = reactive(False)

    def rlog(self, to_print: str) -> None:
        richlog = self.query_one(RichLog)
        richlog.write(to_print)

    def run_chezmoi(self, params: list) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["chezmoi"] + params,
            capture_output=True,
            check=True,
            encoding="utf-8",
            shell=False,
            timeout=1,
        )
        return result

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ButtonSidebar()
            yield CenterContent()
            yield RichLogSidebar()
        yield Footer()

    @on(Button.Pressed, "#chezmoi_config")
    def show_chezmoi_configuration(self):
        self.rlog("[cyan]$ chezmoi cat-config[/]")
        result = self.run_chezmoi(["cat-config"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#chezmoi_status")
    def show_chezmoi_status(self):
        self.rlog("[cyan]$ chezmoi status[/]")
        result = self.run_chezmoi(["status"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#chezmoi_managed")
    def show_chezmoi_managed(self):
        self.rlog("[cyan]$ chezmoi managed[/]")
        result = self.run_chezmoi(["managed"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#clear_richlog")
    def clear_richlog(self):
        self.query_one(RichLog).clear()
        # self.rlog("[green]RichLog Cleared[/]")

    def action_toggle_buttonsidebar(self):
        self.query_one(ButtonSidebar).toggle_class("-hidden")

    def action_toggle_richlogsidebar(self) -> None:
        self.show_richlog = not self.show_richlog

    def watch_show_richlog(self, show_richlog: bool) -> None:
        # Set or unset visible class when reactive changes.
        self.query_one(RichLogSidebar).set_class(show_richlog, "-visible")


if __name__ == "__main__":
    app = ChezmoiTUI()
    app.run()
