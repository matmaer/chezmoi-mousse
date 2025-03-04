from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import DataTable, DirectoryTree, Label, Static


class ChezmoiDoctor(Static):

    def __init__(self, doctor_py_out: list):
        super().__init__()
        self.doctor_py_out = doctor_py_out

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="main_table",
            cursor_type="row",
        )
        yield Label(
            "Local commands skipped because not in Path:",
        )
        yield DataTable(
            id="second_table",
            cursor_type="row",
        )

    # pylint: disable = no-member
    def on_mount(self) -> None:

        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")

        header_row = self.doctor_py_out.pop(0).split()

        main_table.add_columns(*header_row)
        second_table.add_columns(*header_row)

        for row in [row.split(maxsplit=2) for row in self.doctor_py_out]:
            if row[0] == "info" and "not found in $PATH" in row[2]:
                second_table.add_row(*row)
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
                main_table.add_row(*row)


class ChezmoiStatus(Static):
    # Chezmoi status command output reference:
    # https://www.chezmoi.io/reference/commands/status/

    status_table = {
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

    def __init__(self, status_py_out: list):
        super().__init__()
        self.status_py_out = status_py_out

    def compose(self) -> ComposeResult:
        yield Label("Chezmoi Apply Status")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status")
        yield DataTable(id="re_add_table")

    # pylint: disable = no-member
    def on_mount(self):

        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in self.status_py_out:
            path = line[3:]

            apply_status = self.status_table[line[0]]["Status"]
            apply_change = self.status_table[line[0]]["Apply_Change"]

            re_add_status = self.status_table[line[1]]["Status"]
            re_add_change = self.status_table[line[1]]["Re_Add_Change"]

            apply_table.add_row(*[apply_status, path, apply_change])
            re_add_table.add_row(*[re_add_status, path, re_add_change])


class ManagedFiles(DirectoryTree):

    def __init__(self, managed_files: list):
        super().__init__("/home/mm")
        self.managed_paths = [Path(p) for p in managed_files]

    def filter_paths(self, paths):
        return [path for path in paths if path in self.managed_paths]
