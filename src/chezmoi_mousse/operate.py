"""Placeholder for operate screen."""

from textual.screen import Screen
from textual.widgets import Static, Footer


class OperateScreens(Screen):
    def compose(self):
        yield Static("Operate Screen")
        yield Footer()
