from enum import StrEnum

from textual.reactive import reactive
from textual.widgets import Header, Static

from chezmoi_mousse import Chars, Tcss

__all__ = ["CustomHeader", "HeaderTitle"]


class HeaderTitle(StrEnum):
    dry_run_mode = "-  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  -"
    live_mode = "-  c h e z m o i  m o u s s e  --  l i v e  m o d e  -"
    install_help = "- c h e z m o i  m o u s s e  --  i n s t a l l  h e l p  -"


class CustomHeader(Header):

    changes_enabled: reactive[bool] = reactive(False)

    def on_mount(self) -> None:
        self.icon = Chars.burger

    def watch_changes_enabled(self, changes_enabled: bool) -> None:
        if changes_enabled is False:
            self.screen.title = HeaderTitle.dry_run_mode
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.remove_class(Tcss.changes_enabled_color)
            return
        self.screen.title = HeaderTitle.live_mode
        header_title = self.query_exactly_one("HeaderTitle", Static)
        header_title.add_class(Tcss.changes_enabled_color)
