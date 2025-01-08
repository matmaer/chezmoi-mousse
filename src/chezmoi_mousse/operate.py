"""Placeholder for operate screen."""

from pathlib import Path
from typing import Iterable

from textual.screen import Screen
from textual.widget import Widget
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Static, Footer, TabbedContent, DirectoryTree, Header, Pretty

from chezmoi_mousse import chezmoi, CM_CONFIG_DUMP
from chezmoi_mousse.text_blocks import VISUAL_DIAGRAM


class InteractiveDiagram(Widget):
    def __init__(self):
        super().__init__()
        self.text = VISUAL_DIAGRAM

    def compose(self):
        yield Static(self.text)


class ManagedFiles(DirectoryTree):
    def __init__(self):
        super().__init__(CM_CONFIG_DUMP["destDir"])
        self.managed = [Path(entry) for entry in chezmoi.managed()]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]


class OperationTabs(Screen):
    def compose(self):
        with Horizontal():
            yield Header(name="Chezmoi Mousse", show_clock=True)
            with TabbedContent(
                "Diagram",
                "Status",
                "Managed",
            ):
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield Pretty(chezmoi.status())
                with VerticalScroll():
                    yield ManagedFiles()
            yield Footer()
