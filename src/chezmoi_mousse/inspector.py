"""Contains the Textual App class for the TUI."""

from textual.app import ComposeResult


from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Pretty,
    TabbedContent,
)

from chezmoi_mousse import chezmoi

CM_CONFIG_DUMP = chezmoi.dump_config()


class ChezmoiDoctor(DataTable):
    def __init__(self):
        super().__init__()
        self.table = DataTable()
        self.lines = chezmoi.doctor()

    def create_doctor_table(self):
        self.table.add_columns(*self.lines.pop(0).split())
        rows = [row.split(maxsplit=2) for row in self.lines]

        for row in rows:
            if row[0] == "ok":
                row = [f"[#60EE60]{cell}[/]" for cell in row]
            if row[0] == "info":
                if row[2] == "not set":
                    row = [f"[#FFD700]{cell}[/]" for cell in row]
                else:
                    row = [f"[#E0FFFF]{cell}[/]" for cell in row]
            if row[0] == "warning":
                row = [f"[#FFD700]{cell}[/]" for cell in row]
            if row[0] == "error":
                row = [f"[red]{cell}[/]" for cell in row]
            self.table.add_row(*row)
        return self.table


class SettingTabs(Screen):
    def compose(self) -> ComposeResult:
        with TabbedContent(
            "Doctor",
            "Config Dump",
            "Template Data",
            "Config File",
        ):
            yield ChezmoiDoctor().create_doctor_table()
            yield Pretty(CM_CONFIG_DUMP)
            yield Pretty(chezmoi.data())
            yield Pretty(chezmoi.cat_config())
        yield Footer()
