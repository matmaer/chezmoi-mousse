from pathlib import Path
from collections.abc import Iterable

from textual.app import ComposeResult
from textual.widgets import (
    DataTable,
    Static,
    RichLog,
    DirectoryTree,
    Label,
)
from textual.widget import Widget

from chezmoi_mousse.commands import ChezmoiCommands

chezmoi = ChezmoiCommands()


class ChezmoiDoctor(Static):

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="main_table",
            cursor_type = "row",
            classes="tabpad",
        )
        yield Label(
            "Local commands skippeed because not in Path:",
            classes="tabpad",
        )
        yield DataTable(
            id="second_table",
            cursor_type = "row",
            classes="tabpad",
        )

    def on_mount(self):
        self.construct_table()

    def construct_table(self) -> None:
        cm_dr_output = chezmoi.doctor()
        header_row = cm_dr_output.pop(0).split()
        main_rows = []
        other_rows = []
        for row in [row.split(maxsplit=2) for row in cm_dr_output]:
            if row[0] == "info" and " not found in $PATH" in row[2]:
                other_rows.append(row)
            else:
                if row[0] == "ok":
                    row = [f"[#3fc94d]{cell}[/]" for cell in row]
                elif row[0] == "warning":
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                elif row[0] == "error":
                    row = [f"[red]{cell}[/]" for cell in row]
                elif row[0] == "info" and row[2] == "not set":
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                else:
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                main_rows.append(row)

        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")

        main_table.add_columns(*header_row)
        second_table.add_columns(*header_row)
        self.query_one("#main_table").add_rows(main_rows)
        self.query_one("#second_table").add_rows(other_rows)


class ChezmoiStatus(Static):
    """
    Chezmoi status command output reference:
    https://www.chezmoi.io/reference/commands/status/
    """

    status_meaning = {
        "space": {
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
        self.status_output = chezmoi.status()
        self.classes = "tabpad"

    def compose(self) -> ComposeResult:
        yield Label("Chezmoi Apply Status", variant="primary")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status", variant="primary")
        yield DataTable(id="re_add_table")

    def on_mount(self):
        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in self.status_output:
            path = line[3:]

            apply_status = self.status_meaning[line[0]]["Status"]
            apply_change = self.status_meaning[line[0]]["Re_Add_Change"]

            re_add_status = self.status_meaning[line[1]]["Status"]
            re_add_change = self.status_meaning[line[1]]["Apply_Change"]

            apply_row = [apply_status, path, apply_change]
            apply_table.add_row(*apply_row)

            re_add_row = [re_add_status, path, re_add_change]
            re_add_table.add_row(*re_add_row)


class LoggingSlidebar(Widget):
    def __init__(self, highlight: bool = False):
        super().__init__()
        self.id = "command_log"
        self.auto_scroll = True
        self.highlight = highlight
        self.markup = True
        self.max_lines = 2000
        self.wrap = False
        self.animated = True

    def compose(self) -> ComposeResult:
        yield RichLog(id="slidelog")


class ManagedFiles(DirectoryTree):
    def __init__(self):
        # TODO: get destDir from dataclass
        super().__init__("/home/mm")
        self.managed = [Path(entry) for entry in chezmoi.managed()]
        self.classes = "tabpad"

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]
