"""Contains the Textual App class for the TUI."""

# from textual import on
from textual.app import ComposeResult

# from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll

# from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Pretty,
    TabbedContent,
)

from chezmoi_mousse import chezmoi, CM_CONFIG_DUMP


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
                row[0] = f"[#E0FFFF bold]{row[0]}[/]"
                if row[2] == "not set":
                    row[1] = f"[#E0FFFF bold]{row[1]}[/]"
                    row[2] = f"[#FFD700]{row[2]}[/]"
                else:
                    row[1] = f"[#E0FFFF bold]{row[1]}[/]"
                    row[2] = f"[#E0FFFF bold dim]{row[2]}[/]"
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
            yield Header(name="Chezmoi Mousse", show_clock=True)
            with TabbedContent(
                "Doctor",
                "Config-dump",
                "Data",
                "Config-cat",
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


# richlog_visible = reactive(False)

# def rlog(self, to_print: str) -> None:
#     richlog = self.query_one(RichLog)
#     richlog.write(to_print)

# def action_toggle_richlog(self) -> None:
#     self.richlog_visible = not self.richlog_visible

# def watch_richlog_visible(self, richlog_visible: bool) -> None:
#     # Set or unset visible class when reactive changes.
#     self.query_one(MousseLogger).set_class(richlog_visible, "-visible")
