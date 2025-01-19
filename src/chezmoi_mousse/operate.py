"""Placeholder for operate screen."""

from pathlib import Path
from typing import Iterable

from textual.app import ComposeResult
from textual.widget import Widget
from textual.containers import Center
from textual.widgets import (
    Footer,
    TabbedContent,
    DirectoryTree,
    Label,
    Static,
    DataTable,
    LoadingIndicator,
)
from chezmoi_mousse import chezmoi
from chezmoi_mousse.page import PageScreen

CM_CONFIG_DUMP = chezmoi.dump_config()

# provisional diagrams until dynamically created
VISUAL_DIAGRAM = """\
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


class InteractiveDiagram(Widget):
    def __init__(self):
        super().__init__()
        self.diagram = VISUAL_DIAGRAM

    def compose(self):
        yield Center(self.diagram)


class ManagedFiles(DirectoryTree):
    def __init__(self):
        self.config_dump = CM_CONFIG_DUMP
        super().__init__(self.config_dump["destDir"])
        self.managed = [Path(entry) for entry in chezmoi.managed()]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]


class ChezmoiStatus(Static):
    status_meaning = {
        "space": {
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
        self.status_output = chezmoi.status()

    def compose(self) -> ComposeResult:
        yield Label("Chezmoi Apply Status", variant="primary")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status", variant="primary")
        yield DataTable(id="re_add_table")
        yield LoadingIndicator()

    def on_mount(self):
        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        # FIRST COLUMN: difference between the last state written by chezmoi and the actual state
        # SECOND COLUMN: difference between the actual state and the target state, and what effect running chezmoi apply will have
        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in self.status_output:
            path = line[3:]

            apply_status = self.status_meaning[line[0]]["Status"]
            apply_change = self.status_meaning[line[0]]["Re_Add_Change"]

            re_add_status = self.status_meaning[line[1]]["Status"]
            re_add_change = self.status_meaning[line[1]]["Apply_Change"]

            apply_row = [apply_status, path, apply_change]
            apply_table.add_row(*apply_row)

            re_add_row = [re_add_status, path, re_add_change]
            re_add_table.add_row(*re_add_row)


class OperationTabs(PageScreen):
    def compose(self):
        with TabbedContent(
            "Chezmoi-Diagram",
            "Managed-Files",
            "Status-Overview",
        ):
            yield Static(VISUAL_DIAGRAM)
            yield ManagedFiles()
            yield ChezmoiStatus()
        yield Footer()
