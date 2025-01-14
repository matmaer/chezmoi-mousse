"""Contains the Textual App class for the TUI."""

from asyncio import sleep

from textual.app import ComposeResult

from textual import work

from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    LoadingIndicator,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse import chezmoi


class ChezmoiDoctor(Static):
    def __init__(self):
        super().__init__()
        self.cm_dr_output = []

    def compose(self) -> ComposeResult:
        yield DataTable()
        yield LoadingIndicator()

    def on_mount(self):
        data_table = self.query_one(DataTable)
        data_table.loading = True
        self.construct_table(data_table)

    @work
    async def construct_table(self, data_table: DataTable) -> None:
        await sleep(2)  # check how to turn logic below into awaitable
        self.cm_dr_output = chezmoi.doctor()
        data_table.cursor_type = "row"
        header_row = self.cm_dr_output.pop(0).split()
        data_table.add_columns(*header_row)
        rows = [row.split(maxsplit=2) for row in self.cm_dr_output]
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
            data_table.add_row(*row)
        data_table.loading = False


class InspectTabs(Screen):
    def compose(self) -> ComposeResult:
        with TabbedContent(
            "Doctor",
            "Config-Dump",
            "Template-Data",
            "Config-File",
        ):
            yield ChezmoiDoctor()
            yield Pretty(chezmoi.dump_config())
            yield Pretty(chezmoi.data())
            yield Pretty(chezmoi.cat_config())
        yield Footer()
