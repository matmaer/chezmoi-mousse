from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, RichLog


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Button(
            label="chezmoi help",
            id="chezmoi_help",
        )
        yield Button(label="clear rich log", id="clear_richlog")


class ChezMoi(App):
    BINDINGS = [
        ("s", "toggle_sidebar", "MAX"),
        ("q", "quit", "Quit"),
    ]

    CSS_PATH = "textual.tcss"

    def rlog(self, to_print: str) -> None:
        self.query_one(RichLog).write(to_print)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Sidebar(id="sidebar")
            yield RichLog(
                highlight=True,
                wrap=False,
                markup=True,
            )
        yield Footer()

    def action_toggle_sidebar(self):
        self.query_one(Sidebar).toggle_class("-hidden")

    @on(Button.Pressed, "#clear_richlog")
    def chezmoi_help(self):
        self.query_one(RichLog).write("chezmoi_help")

    @on(Button.Pressed, "#clear_richlog")
    def clear_richlog(self):
        self.query_one(RichLog).clear()


def run_tui():
    ChezMoi().run()
