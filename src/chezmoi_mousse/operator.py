from pathlib import Path

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget

from textual.widgets import (
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Label,
    RichLog,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.commands import chezmoi
from chezmoi_mousse.splash import FLOW_DIAGRAM

#pylint: disable=no-member


class SlideBar(Widget):

    def __init__(self, highlight: bool = False):
        super().__init__()
        self.animate = True
        self.auto_scroll = True
        self.highlight = highlight
        self.id = "slidebar"
        self.markup = True
        self.max_lines = 160  # (80×3÷2)×((16−4)÷9)
        self.wrap = True

    def compose(self) -> ComposeResult:
        yield RichLog(id="slidebar-log")

class ChezmoiDoctor(Static):

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

    def on_mount(self) -> None:
        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")

        cm_dr_output = chezmoi.doctor.list_out
        header_row = cm_dr_output.pop(0).split()

        main_table.add_columns(*header_row)
        second_table.add_columns(*header_row)

        for row in [row.split(maxsplit=2) for row in cm_dr_output]:
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

    status_meaning = {
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

    def __init__(self):
        super().__init__()
        self.classes = "tabpad"
        self.status_output = []

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

        for line in chezmoi.status.std_out.splitlines():
            path = line[3:]

            apply_status = self.status_meaning[line[0]]["Status"]
            apply_change = self.status_meaning[line[0]]["Apply_Change"]

            re_add_status = self.status_meaning[line[1]]["Status"]
            re_add_change = self.status_meaning[line[1]]["Re_Add_Change"]

            apply_table.add_row(*[apply_status, path, apply_change])
            re_add_table.add_row(*[re_add_status, path, re_add_change])


class ManagedFiles(DirectoryTree):

    def __init__(self):
        super().__init__("/home/mm")
        self.managed = [
            Path(entry) for entry in chezmoi.managed.list_out
        ]

    def filter_paths(self, paths):
        return [path for path in paths if path in self.managed]


class OperationTabs(Screen):


    BINDINGS = [
        ("s, S", "toggle_sidebar", "Toggle Sidebar"),
    ]

    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header()
        yield SlideBar()
        with TabbedContent(
            "Diagram",
            "Doctor",
            "Dump-Config",
            "Chezmoi-Status",
            "Managed-Files",
            "Template-Data",
            "Cat-Config",
            "Git-Log",
            "Ignored",
            "Git-Status",
            "Unmanaged",
        ):
            yield Static(FLOW_DIAGRAM, id="diagram")
            yield ChezmoiDoctor()
            yield Pretty(chezmoi.dump_config.dict_out)
            yield ChezmoiStatus()
            yield ManagedFiles()
            yield Pretty(chezmoi.data.dict_out)
            yield Pretty(chezmoi.cat_config.list_out)
            yield Pretty(chezmoi.git_log.list_out)
            yield Pretty(chezmoi.ignored.list_out)
            yield Pretty(chezmoi.status.list_out)
            yield Pretty(chezmoi.unmanaged.list_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "- o p e r a t e -"
        self.log_to_slidebar("Welcome to chezmoi-mousse!")

    def log_to_slidebar(self, message: str) -> None:
        self.query_one("#slidebar-log").write(message)

    def action_toggle_sidebar(self) -> None:
        self.show_sidebar = not self.show_sidebar

    def watch_show_sidebar(self, show_sidebar: bool) -> None:
        # Toggle "visible" class when "show_sidebar" reactive changes.
        self.query_one("#slidebar").set_class(show_sidebar, "-visible")
