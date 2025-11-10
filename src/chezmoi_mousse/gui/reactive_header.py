from enum import StrEnum

from textual.reactive import reactive
from textual.widgets import Header, Static

from chezmoi_mousse import AppType, Chars, Tcss

__all__ = ["ReactiveHeader"]


class Titles(StrEnum):
    header_dry_run_mode = (
        " -  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  - "
    )
    header_live_mode = (
        " -  c h e z m o i  m o u s s e  --  l i v e  m o d e  - "
    )


class ReactiveHeader(Header, AppType):

    changes_enabled: reactive[bool | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__(icon=Chars.burger)

    def on_mount(self) -> None:
        self.changes_enabled = self.app.changes_enabled
        if self.changes_enabled is False:
            self.screen.title = Titles.header_dry_run_mode
        elif self.changes_enabled is True:
            self.screen.title = Titles.header_live_mode

    def watch_changes_enabled(self) -> None:
        header_title = self.query_exactly_one("HeaderTitle", Static)
        if self.changes_enabled is True:
            self.screen.title = Titles.header_live_mode
            header_title.add_class(Tcss.changes_enabled_color.name)
        elif self.changes_enabled is False:
            self.screen.title = Titles.header_dry_run_mode
            header_title.remove_class(Tcss.changes_enabled_color.name)
