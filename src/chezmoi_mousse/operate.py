from textual.app import ComposeResult
from textual.containers import Center
from textual.screen import Screen
from textual.widgets import Footer, Static, TabbedContent

from chezmoi_mousse.widgets import ChezmoiStatus, ManagedFiles

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


# TODO move to widgets.py when interactive
class InteractiveDiagram(Static):
    def __init__(self):
        super().__init__()
        self.diagram = VISUAL_DIAGRAM

    def compose(self):
        yield Center(self.diagram)


class OperationTabs(Screen):
    def compose(self) -> ComposeResult:
        with TabbedContent(
            "Chezmoi-Diagram",
            "Managed-Files",
            "Status-Overview",
        ):
            yield Static(VISUAL_DIAGRAM)
            yield ManagedFiles()
            yield ChezmoiStatus()
        yield Footer()
