"""Constructs the Inspector screen."""

import json

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Label,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.commands import run

__all__ = ["InspectTabs"]


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
        yield Header(classes="middle")
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
