"""Contains subclassed textual classes shared between the Logs tab, Config tab
and InstallHelp screen."""

from textual.widget import Widget
from textual.widgets import Collapsible

from chezmoi_mousse import Chars

__all__ = ["CustomCollapsible"]


class CustomCollapsible(Collapsible):

    def __init__(self, *children: Widget, title: str) -> None:
        super().__init__(
            *children,
            title=title,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
        )
