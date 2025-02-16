# pylint: disable=E0401
from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Label,
    Static,
    TabbedContent,
)

from chezmoi_mousse.commands import run
from chezmoi_mousse.graphics import FLOW_DIAGRAM


# class LogSlidebar(Widget):

#     def __init__(self, highlight: bool = False):
#         super().__init__()
#         self.animate = True
#         self.auto_scroll = True
#         self.highlight = highlight
#         self.markup = True
#         self.max_lines = 160  # (80×3÷2)×((16−4)÷9)
#         self.wrap = True

#     def compose(self) -> ComposeResult:
#         with Vertical():
#             yield RichLog(id="richlog-slidebar")


class ChezmoiStatus(Static):
    """
    Chezmoi status command output reference:
    https://www.chezmoi.io/reference/commands/status/
    """

    status_meaning = {
        " ": {
            "Status": "No change",
            "Re_Add_Change": "No change",
            "Apply_Change": "No change",
        },
        "A": {
            "Status": "Added",
            "Re_Add_Change": "Entry was created",
            "Apply_Change": "Entry will be created",
        },
        "D": {
            "Status": "Deleted",
            "Re_Add_Change": "Entry was deleted",
            "Apply_Change": "Entry will be deleted",
        },
        "M": {
            "Status": "Modified",
            "Re_Add_Change": "Entry was modified",
            "Apply_Change": "Entry will be modified",
        },
        "R": {
            "Status": "Run",
            "Re_Add_Change": "Not applicable",
            "Apply_Change": "Entry will be run",
        },
    }

    def __init__(self):
        super().__init__()
        self.classes = "tabpad"
        self.status_output = []

    def compose(self) -> ComposeResult:
        yield Label("Chezmoi Apply Status", variant="primary")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status", variant="primary")
        yield DataTable(id="re_add_table")

    def on_mount(self):
        self.status_output = run("chezmoi", "status").splitlines()
        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in self.status_output:
            path = line[3:]

            apply_status = self.status_meaning[line[0]]["Status"]
            apply_change = self.status_meaning[line[0]]["Apply_Change"]

            re_add_status = self.status_meaning[line[1]]["Status"]
            re_add_change = self.status_meaning[line[1]]["Re_Add_Change"]

            apply_row = [apply_status, path, apply_change]
            apply_table.add_row(*apply_row)

            re_add_row = [re_add_status, path, re_add_change]
            re_add_table.add_row(*re_add_row)


class ManagedFiles(DirectoryTree):

    def __init__(self):
        # TODO: get destDir from dataclass
        super().__init__("/home/mm")
        self.managed = [
            Path(entry) for entry in run("chezmoi", "managed").splitlines()
        ]
        self.classes = "tabpad"

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed = [Path(entry) for entry in self.managed.splitlines()]
        return [path for path in paths if path not in managed]


class OperationTabs(Screen):

    BINDINGS = [
        ("i", "app.push_screen('inspect')", "inspect"),
        ("l", "toggle_sidebar", "command-log"),
    ]

    show_sidebar = reactive(False)

    # def log_to_slidebar(self, message: str) -> None:
    #     self.query_one("#richlog-slidebar").write(message)

    def compose(self) -> ComposeResult:
        yield Header()
        # yield LogSlidebar()
        with Vertical():
            with TabbedContent(
                "Chezmoi-Diagram",
                "Managed-Files",
                "Chezmoi-Status",
                "Git-Status",
            ):
                yield VerticalScroll(Static(FLOW_DIAGRAM, id="diagram"))
                yield ChezmoiStatus()
                yield VerticalScroll(ManagedFiles())
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- o p e r a t e -"

    # def action_toggle_sidebar(self) -> None:
    #     self.show_sidebar = not self.show_sidebar

    # def watch_show_sidebar(self, show_sidebar: bool) -> None:
    #     # Toggle "visible" class when "show_sidebar" reactive changes.
    #     self.query_one("#richlog-slidebar").set_class(show_sidebar, "-visible")
