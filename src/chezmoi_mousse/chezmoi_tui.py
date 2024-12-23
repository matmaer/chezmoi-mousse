import subprocess

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, RichLog

GREETER = """

 ██████╗██╗  ██╗███████╗███████╗███╗   ███╗ ██████╗ ██╗
██╔════╝██║  ██║██╔════╝╚══███╔╝████╗ ████║██╔═══██╗██║
██║     ███████║█████╗    ███╔╝ ██╔████╔██║██║   ██║██║
██║     ██╔══██║██╔══╝   ███╔╝  ██║╚██╔╝██║██║   ██║██║
╚██████╗██║  ██║███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝

 ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗
 ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔════╝
 ██╔████╔██║██║   ██║██║   ██║███████╗███████╗█████╗
 ██║╚██╔╝██║██║   ██║██║   ██║╚════██║╚════██║██╔══╝
 ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████║███████╗
 ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝

"""


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Button(
            label="Status",
            id="chezmoi_status_button",
            tooltip="runs chezmoi status",
        )
        yield Button(
            label="Help",
            id="help_button",
            tooltip="runs chezmoi help",
        )


class ChezmoiTUI(App):
    BINDINGS = [
        ("s", "toggle_sidebar", "Toggle Maximized"),
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "tui.tcss"

    def rlog(self, to_print: str, highlight=True) -> None:
        rich_log = self.query_one(RichLog)
        if not highlight:
            rich_log.highlight = False
        else:
            rich_log.highlight = True
        self.query_one(RichLog).write(to_print)

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
            yield Sidebar(id="sidebar")
            yield RichLog(
                highlight=True,
                wrap=False,
                markup=True,
            )
        yield Footer()

    @on(Button.Pressed, "#chezmoi_status_button")
    def chezmoi_status_button(self):
        self.rlog("Chezmoi status output:")
        result = self.run_chezmoi(["status"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#help_button")
    def help_page(self):
        self.rlog("Chezmoi help output:")
        result = self.run_chezmoi(["help"])
        self.rlog(result.stdout)

    # show the GREETER for just one time
    def on_mount(self):
        self.rlog(GREETER, highlight=False)

    def action_toggle_sidebar(self):
        self.query_one(Sidebar).toggle_class("-hidden")


def run_chezmoi_mousse() -> None:
    ChezmoiTUI().run()


if __name__ == "__main__":
    run_chezmoi_mousse()
