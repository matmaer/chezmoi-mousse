"""Contains the Textual App class for the TUI."""

from textual.app import ComposeResult

from textual.containers import Horizontal, VerticalScroll

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
                row[0] = f"[#90EE90]{row[0]}[/]"
                row[1] = f"[#90EE90]{row[1]}[/]"
                row[2] = f"[#90EE90]{row[2]}[/]"
            if row[0] == "info":
                row[0] = f"[#E0FFFF]{row[0]}[/]"
                if row[2] == "not set":
                    row[1] = f"[#E0FFFF]{row[1]}[/]"
                    row[2] = f"[#FFD700]{row[2]}[/]"
                else:
                    row[0] = f"[#E0FFFF dim]{row[1]}[/]"
                    row[1] = f"[#E0FFFF dim]{row[1]}[/]"
                    row[2] = f"[#E0FFFF dim]{row[2]}[/]"
            if row[0] == "warning":
                row[0] = f"[#FFD700]{row[0]}[/]"
                row[1] = f"[#FFD700]{row[1]}[/]"
                row[2] = f"[#FFD700]{row[2]}[/]"
            if row[0] == "error":
                row[0] = f"[red]{row[0]}[/]"
                row[1] = f"[red]{row[1]}[/]"
                row[2] = f"[red]{row[2]}[/]"
            self.table.add_row(*row)
        return self.table


class SettingTabs(Screen):
    def compose(self) -> ComposeResult:
        with Horizontal():
            with TabbedContent(
                "Doctor",
                "Config Dump",
                "Template Data",
                "Config File",
            ):
                with VerticalScroll():
                    yield ChezmoiDoctor().create_doctor_table()
                with VerticalScroll():
                    yield Pretty(CM_CONFIG_DUMP)
                with VerticalScroll():
                    yield Pretty(chezmoi.data())
                with VerticalScroll():
                    yield Pretty(chezmoi.cat_config())
            yield Footer()
