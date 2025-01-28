from pathlib import Path
from collections.abc import Iterable

from textual import work
from textual.app import ComposeResult
from textual.widgets import (
    DataTable,
    LoadingIndicator,
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
            id="doctor",
            cursor_type = "row",
            classes="horipad",
            )
        yield LoadingIndicator()

    def on_mount(self):
        data_table = self.query_one("#doctor")
        data_table.loading = True
        self.construct_table()

    @work(thread=True)
    def construct_table(self) -> None:
        data_table = self.query_one("#doctor")
        # TODO get chezmoi.doctor output from dataclass
        cm_dr_output = chezmoi.doctor()
        header_row = cm_dr_output.pop(0).split()
        data_table.add_columns(*header_row)
        rows = [row.split(maxsplit=2) for row in cm_dr_output]
        for row in rows:
            if row[0] == "ok":
                row = [f"[#60EE60]{cell}[/]" for cell in row]
            if row[0] == "info":
                if row[2] == "not set":
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                elif "not found in $PATH" in row[2]:
                    row = [f"[#8A8888]{cell}[/]" for cell in row]
                else:
                    row = [f"[#E0FFFF]{cell}[/]" for cell in row]
            if row[0] == "warning":
                row = [f"[#FFD700]{cell}[/]" for cell in row]
            if row[0] == "error":
                row = [f"[red]{cell}[/]" for cell in row]
            data_table.add_row(*row)
        data_table.loading = False


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
        # TODO read from dataclass
        self.status_output = chezmoi.status()
        self.classes = "horipad"

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
        self.classes = "horipad"

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]
