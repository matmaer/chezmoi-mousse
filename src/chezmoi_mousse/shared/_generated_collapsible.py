"""Contains subclassed textual classes shared between the Logs tab and the
Config tab."""

from typing import TYPE_CHECKING

from textual.widgets import Collapsible

from chezmoi_mousse import AppType, Chars, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["GeneratedCollapsible"]


class GeneratedCollapsible(Collapsible, AppType):

    def __init__(
        self, ids: "CanvasIds", counter: int, title_color: str | None = None
    ) -> None:
        super().__init__(
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
            id=ids.generated_collapsible_id(counter=counter),
            classes=Tcss.custom_collapsible.name,
        )

        if title_color is None:
            self.title_color = self.app.theme_variables["primary-lighten-3"]
        else:
            self.title_color = title_color

    def on_mount(self) -> None:
        collapsible_title = self.query_exactly_one("CollapsibleTitle")
        collapsible_title.styles.color = self.title_color
