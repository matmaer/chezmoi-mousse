"""Placeholder for operate screen."""

from pathlib import Path
from typing import Iterable

from textual.widget import Widget
from textual.containers import Center
from textual.widgets import Footer, TabbedContent, DirectoryTree, Pretty, Static
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
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │   chezmoi apply   │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │  chezmoi status   │                   │                   │
       │   chezmoi diff    │                   │                   │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─ │                   │     git push      │
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


class OperationTabs(PageScreen):
    def compose(self):
        with TabbedContent(
            "Chezmoi-Diagram",
            "Managed-Files",
            "Status-Overview",
        ):
            yield Static(VISUAL_DIAGRAM)
            yield ManagedFiles()
            yield Pretty(chezmoi.status())
        yield Footer()
