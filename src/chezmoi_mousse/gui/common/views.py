from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea

from chezmoi_mousse import AppIds, AppType, Tcss

if TYPE_CHECKING:
    from textual.widgets import DataTable

__all__ = ["ContentsView", "DiffView", "GitLog"]

type DiffWidgets = list[Label | Static]


class ContentsView(Vertical, AppType):

    content_widgets: reactive["Static | TextArea | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        assert self.app.paths is not None
        self.border_title = f" {self.app.paths.dest_dir} "

    def watch_content_widgets(self) -> None:
        if self.content_widgets is None:
            return
        self.remove_children()
        self.mount(self.content_widgets)


class DiffView(ScrollableContainer, AppType):

    diff_widgets: reactive["list[Static] | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        if self.app.paths is None:
            raise ValueError("self.app.paths is None in DiffView on_mount")
        self.border_title = f" {self.app.paths.dest_dir} "

    def watch_diff_widgets(self) -> None:
        if self.diff_widgets is None:
            return
        self.remove_children()
        self.mount_all(self.diff_widgets)


class GitLog(ScrollableContainer, AppType):

    git_log_result: reactive["DataTable[str] | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.git_log, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        if self.app.paths is None:
            raise ValueError("self.app.paths is None in GitLog on_mount")
        self.border_title = f" {self.app.paths.dest_dir} "

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return
        self.remove_children()
        self.mount(self.git_log_result)
