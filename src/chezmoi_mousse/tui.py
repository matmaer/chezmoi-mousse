""" Contains the Textual App class for the TUI. """

# from pathlib import Path
# from typing import Iterable
from textual import on
from textual.app import App, ComposeResult, Widget
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (Button, DirectoryTree, Footer, Header, Pretty,
                             RichLog, Static, TabbedContent)

from chezmoi_mousse import CHEZMOI_CONFIG
from chezmoi_mousse.common import run_chezmoi
from chezmoi_mousse.diagrams import VISUAL_DIAGRAM


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


# class GlobalsLocals(VerticalScroll):
#     def compose(self) -> ComposeResult:
#         yield Pretty(locals(), name="Locals")
#         yield Pretty(globals(), name="Globals")


# class ManagedFiles(DirectoryTree):
#     def __init__(self):
#         super().__init__(Path(CHEZMOI_CONFIG["destDir"]))
#         self.to_filter = []
#         self.filtered_paths = []

#     def get_chezmoi_managed(self):
#         chezmoi_arguments = [
#             "managed",
#             "--exclude=dirs",
#             "--path-style=absolute",
#             ]
#         cm_managed = run_chezmoi(chezmoi_arguments).stdout.splitlines()
#         self.to_filter = [Path(p) for p in cm_managed]

#     def filter_paths(self):
#         for path in self.to_filter:
#             if path.name in self.to_filter:
#                 self.filtered_paths.append(path)
#         return self.filtered_paths


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

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ButtonSidebar()
            with TabbedContent(
                "Destination",
                "Diagram",
                "Globals",
                "Locals",
            ):
                yield DirectoryTree(CHEZMOI_CONFIG["destDir"])
                # yield DirectoryTree(Iterable[CHEZMOI_MANAGED])
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield Pretty(globals(), name="Globals")
                with VerticalScroll():
                    yield Pretty(locals(), name="Lobals")

            yield RichLogSidebar()
        yield Footer()

    @on(Button.Pressed, "#chezmoi_config")
    def show_chezmoi_configuration(self):
        self.rlog("[cyan]$ chezmoi cat-config[/]")
        result = run_chezmoi(["cat-config"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#chezmoi_status")
    def show_chezmoi_status(self):
        self.rlog("[cyan]$ chezmoi status[/]")
        result = run_chezmoi(["status"])
        self.rlog(result.stdout)

    @on(Button.Pressed, "#chezmoi_managed")
    def show_chezmoi_managed(self):
        self.rlog("[cyan]$ chezmoi managed[/]")
        result = run_chezmoi(["managed"])
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
