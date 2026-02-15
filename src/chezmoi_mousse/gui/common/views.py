from typing import TYPE_CHECKING

from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from chezmoi_mousse import AppIds, AppType, Tcss

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ContentsView"]

type GitLogTableDict = dict[Path, DataTable[str]]
type DiffWidgetDict = dict[Path, list[Static]]


class ContentsView(Vertical, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        self.border_title = f" {self.app.cmd_results.dest_dir} "

    def watch_path(self) -> None:
        if self.path is None:
            return
        if self.app.paths is None:
            raise ValueError("self.app.paths is None in ContentsView watch_path")
        self.remove_children()
        self.mount(self.app.paths.contents_dict[self.path])
