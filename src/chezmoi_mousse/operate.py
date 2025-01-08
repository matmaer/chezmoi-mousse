"""Placeholder for operate screen."""

from textual.screen import Screen
from textual.widgets import Static, Footer

from chezmoi_mousse.text_blocks import VISUAL_DIAGRAM


class OperationTabs(Screen):
    def compose(self):
        yield Static(VISUAL_DIAGRAM)
        yield Footer()
