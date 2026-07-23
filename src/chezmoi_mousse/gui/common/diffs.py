from __future__ import annotations

from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import ReadCmd, StatusCode, TabLabel, Tcss

from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui

__all__ = ["DiffView"]

DIFF_TCSS = {
    " ": Tcss.context,
    "@@": Tcss.context,
    "index": Tcss.context,
    "-": Tcss.removed,
    "deleted": Tcss.removed,
    "old": Tcss.removed,
    "+": Tcss.added,
    "new": Tcss.added,
    "changed": Tcss.changed,
    "unhandled": Tcss.unhandled,
}


class DiffView(Container):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        self.ids = ids
        super().__init__(id=ids.container.diff)

    def _create_diff_widgets(self, path: Path) -> list[Label | Static]:
        widgets: list[Label | Static] = []
        if self.ids.tab_label == TabLabel.apply:
            diff_result = self.app.cm_attr.command.run(
                dry_run=False, cmd=ReadCmd.diff, path_arg=path
            )
        else:  # re-add tab
            diff_result = self.app.cm_attr.command.run(
                dry_run=False, cmd=ReadCmd.diff_reverse, path_arg=path
            )
        self.post_message(LogCmdResultMsg(diff_result))
        diff_lines = diff_result.std_out.splitlines()
        if not diff_lines:
            return [Static("No diff output available.", classes=Tcss.info)]
        diff_cmd = diff_lines.pop(0)
        widgets.append(Label(diff_cmd, classes=Tcss.flat_section_label))

        def get_prefix(line: str) -> str:
            for p in DIFF_TCSS:
                if line.startswith(p):
                    return p
            return "unhandled"

        for prefix, group_lines in groupby(diff_lines, key=get_prefix):
            group_list = list(group_lines)
            if prefix in ("+", "-"):
                text = "\n".join(group_list)
                widgets.append(
                    Static(text, classes=DIFF_TCSS[prefix].value, markup=False)
                )
            else:
                for line in group_list:
                    widgets.append(
                        Static(line, classes=DIFF_TCSS[prefix].value, markup=False)
                    )
        return widgets

    def _get_status_dirs(self) -> dict[Path, StatusCode]:
        return {}

    def _get_status_dir_descendants(self, dir_path: Path) -> dict[Path, StatusCode]:
        status_dirs = self._get_status_dirs()
        results: dict[Path, StatusCode] = {}
        for path, status in status_dirs.items():
            if path.is_relative_to(dir_path):
                results[path] = status
        return results

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.remove_children()
        widgets: list[Label | Static] = self._create_diff_widgets(show_path)
        container = ScrollableContainer(*widgets)
        self.mount(container)
