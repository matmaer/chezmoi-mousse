import subprocess

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, RichLog, Static

GREETER_PART_1 = """
 ██████╗██╗  ██╗███████╗███████╗███╗   ███╗ ██████╗ ██╗
██╔════╝██║  ██║██╔════╝╚══███╔╝████╗ ████║██╔═══██╗██║
██║     ███████║█████╗    ███╔╝ ██╔████╔██║██║   ██║██║
██║     ██╔══██║██╔══╝   ███╔╝  ██║╚██╔╝██║██║   ██║██║
╚██████╗██║  ██║███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝
 """
GREETER_PART_2 = """
 ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗
 ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔════╝
 ██╔████╔██║██║   ██║██║   ██║███████╗███████╗█████╗
 ██║╚██╔╝██║██║   ██║██║   ██║╚════██║╚════██║██╔══╝
 ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████║███████╗
 ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
"""
VISUAL_DIAGRAM = """
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │    chezmoi add    │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │   chezmoi apply   │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  chezmoi status   │                   │                   │
       │   chezmoi diff    │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─ │                   │     git push      │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │           chezmoi git pull            │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │                   │    git commit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │    autoCommit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                autoPush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""


class ButtonSidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Button(
            label="Status",
            id="chezmoi_status",
        )
        yield Button(
            label="Chezmoi Managed",
            id="chezmoi_managed",
            tooltip="List the managed files in the home directory",
        )
        yield Button(
            label="Clear RichLog",
            id="clear_richlog",
        )
        yield Button(
            label="Help",
            id="app_help",
        )


class RichLogSidebar(Vertical):
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
        ("b", "toggle_buttonsidebar", "Toggle Buttons Sidebar"),
        ("r", "toggle_richlogsidebar", "Toggle Shell Output Sidebar"),
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "tui.tcss"

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
            yield ButtonSidebar(id="button_sidebar")
            yield CenterContent()
            yield RichLogSidebar()
        yield Footer()

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
        # debug message
        self.rlog("[green]RichLog Cleared[/]")

    @on(Button.Pressed, "#app_help")
    def help_page(self):
        self.rlog("$ chezmoi help")
        result = self.run_chezmoi(["help"])
        self.rlog(result.stdout)

    # show the greeter after startup
    def on_mount(self):
        top_lines = GREETER_PART_1.split("\n")
        bottom_lines = GREETER_PART_2.split("\n")
        gradient = [
            "#439CFB",
            "#6698FB",
            "#8994FB",
            "#AB8FFB",
            "#CE8BFB",
            "#F187FB",
            "#F187FB",
        ]
        for line, color in zip(top_lines, gradient):
            self.rlog(f"[{color}]{line}[/]")
        gradient.reverse()
        for line, color in zip(bottom_lines, gradient):
            self.rlog(f"[{color}]{line}[/]")
        self.rlog(" ")

    def action_toggle_buttonsidebar(self):
        self.query_one(ButtonSidebar).toggle_class("-hidden")

    def action_toggle_richlogsidebar(self):
        self.query_one(RichLogSidebar).toggle_class("-hidden")


if __name__ == "__main__":
    app = ChezmoiTUI()
    app.run()
