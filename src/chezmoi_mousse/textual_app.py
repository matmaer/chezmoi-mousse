import subprocess

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, RichLog  # , DirectoryTree

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


# class ManagedFiles(DirectoryTree):
#     managed =
#     def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
#         return [path for path in paths if not path.name.startswith(".")]


class ChezmoiTUI(App):
    BINDINGS = [
        ("b", "toggle_buttonsidebar", "Toggle Buttons Sidebar"),
        ("r", "toggle_richlogsidebar", "Toggle Shell Output Sidebar"),
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
            yield ButtonSidebar(id="button_sidebar")
            # yield Static(VISUAL_DIAGRAM)
            # yield DirectoryTree()
            yield RichLogSidebar()
        yield Footer()

    @on(Button.Pressed, "#chezmoi_status")
    def show_chezmoi_status(self):
        self.rlog("Chezmoi status output:")
        result = self.run_chezmoi(["status"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#chezmoi_managed")
    def show_chezmoi_managed(self):
        # debug message
        self.rlog("Chezmoi managed output:")
        result = self.run_chezmoi(["managed"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#clear_richlog")
    def clear_richlog(self):
        self.query_one(RichLog).clear()
        # debug message
        self.rlog("[cyan]RichLog Cleared[/]")

    # @on(Button.Pressed, "#help")
    # def help_page(self):
    #     self.rlog("Chezmoi help output:")
    #     result = self.run_chezmoi(["help"])
    #     self.rlog(result.stdout)

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
            text = Text.from_markup(f"[{color}]{line}[/]")
            self.query_one(RichLog).write(text)
        gradient.reverse()
        for line, color in zip(bottom_lines, gradient):
            text = Text.from_markup(f"[{color}]{line}[/]")
            self.query_one(RichLog).write(text)
        self.rlog(" ")

    def action_toggle_buttonsidebar(self):
        self.query_one(ButtonSidebar).toggle_class("-hidden")

    def action_toggle_richlogsidebar(self):
        self.query_one(RichLogSidebar).toggle_class("-hidden")


def run_chezmoi_mousse() -> None:
    ChezmoiTUI().run()


if __name__ == "__main__":
    run_chezmoi_mousse()
