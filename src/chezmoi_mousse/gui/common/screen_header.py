from enum import StrEnum
from typing import TYPE_CHECKING

from textual.reactive import reactive
from textual.widgets import Header, Static

from chezmoi_mousse import AppType, Chars, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["CustomHeader", "HeaderTitle"]


class HeaderTitle(StrEnum):
    read_mode = "-  c h e z m o i  m o u s s e  --  r e a d  m o d e  -"
    dry_run_mode = "-  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  -"
    live_mode = "-  c h e z m o i  m o u s s e  --  l i v e  m o d e  -"
    install_help = "- c h e z m o i  m o u s s e  --  i n s t a l l  h e l p  -"


class CustomHeader(Header, AppType):

    read_mode: reactive[bool] = reactive(True)
    changes_enabled: reactive[bool] = reactive(False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.header)

    def on_mount(self) -> None:
        self.icon = Chars.burger
        self.screen.title = HeaderTitle.read_mode

    def watch_read_mode(self) -> None:
        if self.read_mode is True:
            self.screen.title = HeaderTitle.read_mode
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.remove_class(Tcss.changes_enabled_color)
        else:
            self.watch_changes_enabled()

    def watch_changes_enabled(self) -> None:
        if self.read_mode is True:
            return
        if self.changes_enabled is True:
            self.screen.title = HeaderTitle.live_mode
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.add_class(Tcss.changes_enabled_color)
        elif self.changes_enabled is False:
            self.screen.title = HeaderTitle.dry_run_mode
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.remove_class(Tcss.changes_enabled_color)
