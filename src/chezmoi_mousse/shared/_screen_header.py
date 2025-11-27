from typing import TYPE_CHECKING

from textual.reactive import reactive
from textual.widgets import Header, Static

from chezmoi_mousse import AppType, Chars, HeaderTitle, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["CustomHeader"]


class CustomHeader(Header, AppType):

    changes_enabled: reactive[bool | None] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(icon=Chars.burger, id=ids.header)

    def on_mount(self) -> None:
        self.changes_enabled = self.app.changes_enabled
        if self.changes_enabled is False:
            self.screen.title = HeaderTitle.header_dry_run_mode
        elif self.changes_enabled is True:
            self.screen.title = HeaderTitle.header_live_mode

    def watch_changes_enabled(self) -> None:
        header_title = self.query_exactly_one("HeaderTitle", Static)
        if self.changes_enabled is True:
            self.screen.title = HeaderTitle.header_live_mode
            header_title.add_class(Tcss.changes_enabled_color)
        elif self.changes_enabled is False:
            self.screen.title = HeaderTitle.header_dry_run_mode
            header_title.remove_class(Tcss.changes_enabled_color)
