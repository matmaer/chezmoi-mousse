# from collections.abc import Iterable
# from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import DataTable, Label, Static


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


# class ManagedFiles(DirectoryTree):
# Initialise the managed files widget.
# def __init__(
#     self,
#     paths: list[Path],
#     widget_id="managed_files_widget",
# ) -> None:
#     """Initialise the directory tree."""
#     super().__init__(
#         path=chezmoi.dest_dir,
#         id=widget_id,
#     )
#     self.paths = paths

#     self._initialize_tree()

# def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
#     return [path for path in paths if path in self.paths]

# def _initialize_tree(self) -> None:
#     # apply filter
#     self.filter_paths(self.paths)
#     # Clear the current tree nodes
#     self.clear_node(self.root)
#     # Reload the tree to reflect the changes
#     self.reload()

# chezmoi.managed.update()
# managed = [Path(path) for path in chezmoi.managed.py_out]
# [Path(path) for path in chezmoi.unmanaged.py_out]
