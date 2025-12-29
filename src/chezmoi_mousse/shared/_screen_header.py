from enum import StrEnum
from typing import TYPE_CHECKING

from textual.reactive import reactive
from textual.widgets import Header, Static

from chezmoi_mousse import AppType, Chars, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["CustomHeader", "HeaderTitle"]


class HeaderTitle(StrEnum):
    header_dry_run_mode = (
        " -  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  - "
    )
    header_live_mode = (
        " -  c h e z m o i  m o u s s e  --  l i v e  m o d e  - "
    )
    header_install_help = (
        " - c h e z m o i  m o u s s e  --  i n s t a l l  h e l p  - "
    )


class CustomHeader(Header, AppType):

    changes_enabled: reactive[bool | None] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.header)

    def on_mount(self) -> None:
        self.icon = Chars.burger
        if self.app.changes_enabled is False:
            self.screen.title = HeaderTitle.header_dry_run_mode
        elif self.app.changes_enabled is True:
            self.screen.title = HeaderTitle.header_live_mode

    def watch_changes_enabled(self) -> None:
        header_title = self.query_exactly_one("HeaderTitle", Static)
        if self.changes_enabled is True:
            self.screen.title = HeaderTitle.header_live_mode
            header_title.add_class(Tcss.changes_enabled_color)
        elif self.changes_enabled is False:
            self.screen.title = HeaderTitle.header_dry_run_mode
            header_title.remove_class(Tcss.changes_enabled_color)
