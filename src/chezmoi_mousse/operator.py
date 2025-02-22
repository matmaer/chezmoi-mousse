import json
# pylint: disable=E0401
from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    DirectoryTree,
    Footer,
    Header,
    Label,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.commands import chezmoi_config, run

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

    def on_mount(self):
        self.construct_table()

    def construct_table(self) -> None:
        cm_dr_output = run("doctor").splitlines()
        header_row = cm_dr_output.pop(0).split()
        main_rows = []
        other_rows = []
        for row in [row.split(maxsplit=2) for row in cm_dr_output]:
            if row[0] == "info" and "not found in $PATH" in row[2]:
                other_rows.append(row)
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
                main_rows.append(row)

        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")

        main_table.add_columns(*header_row)
        second_table.add_columns(*header_row)
        main_table.add_rows(main_rows)
        second_table.add_rows(other_rows)


class InspectTabs(Screen):

    BINDINGS = [
        ("o, O", "app.push_screen('operate')", "operate"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with TabbedContent(
                "Doctor",
                "Config-Dump",
                "Template-Data",
                "Config-File",
                "Ignored",
                "Git-Status",
                "Git-Log",
            ):
                yield VerticalScroll(ChezmoiDoctor())
                yield VerticalScroll(Pretty(json.loads(run("dump_config"))))
                yield VerticalScroll(Pretty(json.loads(run("data"))))
                yield VerticalScroll(Pretty(run("cat_config").splitlines()))
                yield VerticalScroll(Pretty(run("ignored").splitlines()))
                yield VerticalScroll(Pretty(run("git_status").splitlines()))
                yield VerticalScroll(Pretty(run("git_log").splitlines()))
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- i n s p e c t -"



# provisional diagrams until dynamically created
FLOW_DIAGRAM = """\
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│home directory│    │ working copy │    │  local repo  │    │ remote repo  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │    chezmoi add    │                   │                   │
       │   chezmoi re-add  │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │   chezmoi apply   │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  chezmoi status   │                   │                   │
       │   chezmoi diff    │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─>│                   │     git push      │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │           chezmoi git pull            │
       │                   │<──────────────────────────────────────│
       │                   │                   │                   │
       │                   │    git commit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │    autoCommit     │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                autoPush               │
       │                   │──────────────────────────────────────>│
       │                   │                   │                   │
       │                   │                   │                   │
┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐    ┌──────┴───────┐
│ destination  │    │   staging    │    │   git repo   │    │  git remote  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
"""

# class LogSlidebar(Widget):

#     def __init__(self, highlight: bool = False):
#         super().__init__()
#         self.animate = True
#         self.auto_scroll = True
#         self.highlight = highlight
#         self.markup = True
#         self.max_lines = 160  # (80×3÷2)×((16−4)÷9)
#         self.wrap = True

#     def compose(self) -> ComposeResult:
#         with Vertical():
#             yield RichLog(id="richlog-slidebar")


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
        yield Label("Chezmoi Apply Status", variant="primary")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status", variant="primary")
        yield DataTable(id="re_add_table")

    def on_mount(self):
        self.status_output = run("status").splitlines()
        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in self.status_output:
            path = line[3:]

            apply_status = self.status_meaning[line[0]]["Status"]
            apply_change = self.status_meaning[line[0]]["Apply_Change"]

            re_add_status = self.status_meaning[line[1]]["Status"]
            re_add_change = self.status_meaning[line[1]]["Re_Add_Change"]

            apply_row = [apply_status, path, apply_change]
            apply_table.add_row(*apply_row)

            re_add_row = [re_add_status, path, re_add_change]
            re_add_table.add_row(*re_add_row)


class ManagedFiles(DirectoryTree):

    def __init__(self):
        super().__init__(chezmoi_config["destDir"])
        self.managed = [Path(entry) for entry in run("managed").splitlines()]
        self.classes = "tabpad"

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]


class OperationTabs(Screen):

    BINDINGS = [
        ("l, L", "toggle_sidebar", "command-log"),
    ]

    show_sidebar = reactive(False)

    # def log_to_slidebar(self, message: str) -> None:
    #     self.query_one("#richlog-slidebar").write(message)

    def compose(self) -> ComposeResult:
        yield Header()
        # yield LogSlidebar()
        with Vertical():
            with TabbedContent(
                "Chezmoi-Diagram",
                "Chezmoi-Status",
                "Managed-Files",
            ):
                yield VerticalScroll(Static(FLOW_DIAGRAM, id="diagram"))
                yield ChezmoiStatus()
                yield VerticalScroll(ManagedFiles())
        yield Footer()

    def on_mount(self) -> None:
        self.title = "- o p e r a t e -"

    # def action_toggle_sidebar(self) -> None:
    #     self.show_sidebar = not self.show_sidebar

    # def watch_show_sidebar(self, show_sidebar: bool) -> None:
    #     # Toggle "visible" class when "show_sidebar" reactive changes.
    #     self.query_one("#richlog-slidebar").set_class(show_sidebar, "-visible")
