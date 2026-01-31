from enum import StrEnum
from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import AppIds, AppType, Tcss
from chezmoi_mousse._widget_factory import DirContentWidgets, FileContentWidgets

if TYPE_CHECKING:
    from textual.widgets import DataTable

__all__ = ["ContentsView", "DiffView", "GitLog"]

type DiffWidgets = list[Label | Static]


class ContentsView(Vertical, AppType):

    content_widgets: reactive["FileContentWidgets | DirContentWidgets | None"] = (
        reactive(None, init=False)
    )

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.contents, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        # TODO: make this configurable but should be reasonable truncate for
        # displaying enough of a file to judge operating on it.
        self.truncate_size = self.app.max_file_size // 10
        self.border_title = f" {self.app.dest_dir} "

    def watch_content_widgets(self) -> None:
        if self.content_widgets is None:
            return
        if self.app.dest_dir is None:
            raise ValueError(
                "self.app.dest_dir is None in ContentsView.watch_node_data"
            )
        self.remove_children()
        self.mount(self.content_widgets.widget)


class DiffStrings(StrEnum):
    contains_no_status_paths = "Contains no paths with a status."
    dir_no_status = (
        "[dim]No diff available, the directory has no status and "
        "contains no paths with a status.[/]"
    )
    file_diff_lines = "File Diff Lines"
    file_no_status = "[dim]No diff available, the file has no status.[/]"
    mode_changes = "Mode Differences"
    path_lines = "Path Differences"
    truncated = "\n--- Diff output truncated to 1000 lines ---\n"


class DiffView(ScrollableContainer, AppType):

    diff_widgets: reactive["list[Static] | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        self.border_title = f" {self.app.dest_dir} "

    def watch_diff_widgets(self) -> None:
        if self.diff_widgets is None:
            return
        self.remove_children()
        self.mount_all(self.diff_widgets)


class GitLog(ScrollableContainer, AppType):

    git_log_result: reactive["DataTable[str] | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.git_log, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        self.border_title = f" {self.app.dest_dir} "

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return
        self.remove_children()
        self.mount(self.git_log_result)
