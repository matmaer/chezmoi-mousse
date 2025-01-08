"""Placeholder for operate screen."""

from pathlib import Path
from typing import Iterable

from textual.screen import Screen
from textual.widget import Widget
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Static, Footer, TabbedContent, DirectoryTree, Header, Pretty

from chezmoi_mousse import chezmoi

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
        yield Static(self.diagram)


class ManagedFiles(DirectoryTree):
    def __init__(self):
        self.config_dump = CM_CONFIG_DUMP
        super().__init__(self.config_dump["destDir"])
        self.managed = [Path(entry) for entry in chezmoi.managed()]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]


class OperationTabs(Screen):
    def compose(self):
        with Horizontal():
            yield Header(name="Chezmoi Operations")
            with TabbedContent(
                "Chezmoi Diagram",
                "Managed Files",
                "Status Overview",
            ):
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield ManagedFiles()
                with VerticalScroll():
                    yield Pretty(chezmoi.status())
            yield Footer()
