from textual import work
from textual.app import ComposeResult
from textual.widgets import DataTable, LoadingIndicator, Static, RichLog
from textual.widget import Widget

from chezmoi_mousse.commands import ChezmoiCommands

chezmoi = ChezmoiCommands()


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
        # TODO get from shared object that stores all output
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
