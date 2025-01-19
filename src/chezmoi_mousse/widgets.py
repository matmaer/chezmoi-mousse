from textual import work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import DataTable, LoadingIndicator, Static, Label, Pretty
from chezmoi_mousse import chezmoi


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


class VariablesScreen(ModalScreen):
    DEFAULT_CSS = """
    VariablesScreen {
        #vars {
            border: heavy $accent;
            margin: 2 4;
            scrollbar-gutter: stable;
            Static {
                width: auto;
            }
        }
    }
    """
    BINDINGS = [("escape", "dismiss", "Dismiss")]

    def __init__(self, local_vars: dict, global_vars: dict) -> None:
        super().__init__()
        self.local_vars = local_vars
        self.global_vars = global_vars
        if "__builtins__" in self.global_vars:
            del self.global_vars["__builtins__"]
        if "__cached__" in self.global_vars:
            del self.global_vars["__cached__"]

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="vars"):
            yield Label("Global Variables", variant="primary")
            yield Pretty(self.global_vars)
            yield Label("Local Variables", variant="primary")
            yield Pretty(self.local_vars)

    def on_mount(self):
        code_widget = self.query_one("#vars")
        code_widget.border_title = "Variables"
        code_widget.border_subtitle = "Escape to close"
