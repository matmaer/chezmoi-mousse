"""Contains subclassed textual classes shared between the Logs tab and the
Config tab."""

from textual.widget import Widget
from textual.widgets import Collapsible

from chezmoi_mousse import Chars, Tcss

__all__ = ["CustomCollapsible"]


class CustomCollapsible(Collapsible):

    def __init__(self, *children: Widget, title: str = "Toggle") -> None:
        super().__init__(
            *children,
            title=title,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
            classes=Tcss.custom_collapsible.name,
        )
