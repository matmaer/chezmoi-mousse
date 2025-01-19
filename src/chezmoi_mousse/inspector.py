"""Contains the Inspector Screen."""

from textual import work
from textual.app import ComposeResult
from textual.widgets import (
    DataTable,
    Footer,
    LoadingIndicator,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse import chezmoi
from chezmoi_mousse.page import PageScreen


class ChezmoiDoctor(Static):
    def compose(self) -> ComposeResult:
        yield DataTable(id="doctor")
        yield LoadingIndicator()

    def on_mount(self):
        data_table = self.query_one("#doctor")
        data_table.loading = True
        self.construct_table()

    @work(thread=True)
    def construct_table(self) -> None:
        data_table = self.query_one("#doctor")
        cm_dr_output = chezmoi.doctor()
        data_table.cursor_type = "row"
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


class InspectTabs(PageScreen):
    def compose(self) -> ComposeResult:
        with TabbedContent(
            "Doctor",
            "Config-Dump",
            "Template-Data",
            "Config-File",
            "State-Dump",
            "Target-State",
            "Ignored",
        ):
            yield ChezmoiDoctor()
            yield Pretty(chezmoi.dump_config())
            yield Pretty(chezmoi.data())
            yield Pretty(chezmoi.cat_config())
            yield Pretty(chezmoi.state_dump())
            yield Pretty(chezmoi.target_state_dump())
            yield Pretty(chezmoi.ignored())
        yield Footer()
