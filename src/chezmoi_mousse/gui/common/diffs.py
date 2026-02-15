from itertools import groupby
from pathlib import Path

from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Static

from chezmoi_mousse import (
    CMD,
    AppIds,
    AppType,
    CommandResult,
    LogString,
    ReadCmd,
    TabName,
    Tcss,
)

__all__ = ["DiffView"]

type DiffWidgetDict = dict[Path, list[Static]]


DIFF_TCSS = {
    "diff --git a/": Tcss.command,
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


class DiffView(ScrollableContainer, AppType):

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff, classes=Tcss.border_title_top)
        self.cache: DiffWidgetDict = {}
        self.canvas_name = ids.canvas_name

    def on_mount(self) -> None:
        self.border_title = f" {self.app.cmd_results.dest_dir} "

    def create_diff_widgets(self, diff_result: CommandResult) -> list[Static]:
        if not diff_result.std_out:
            return [Static(LogString.no_stdout)]

        widgets: list[Static] = []
        lines = diff_result.std_out.splitlines()

        def get_prefix(line: str) -> str:
            for p in DIFF_TCSS:
                if line.startswith(p):
                    return p
            return "unhandled"

        for prefix, group_lines in groupby(lines, key=get_prefix):
            group_list = list(group_lines)
            if prefix in ("+", "-"):
                text = "\n".join(group_list)
                widgets.append(Static(text, classes=DIFF_TCSS[prefix].value))
            else:
                for line in group_list:
                    widgets.append(Static(line, classes=DIFF_TCSS[prefix].value))
        return widgets

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return
        if self.canvas_name == TabName.apply and self.show_path not in self.cache:
            self.cache[self.show_path] = self.create_diff_widgets(
                CMD.read(ReadCmd.diff, path_arg=self.show_path)
            )

        elif self.canvas_name == TabName.re_add and self.show_path not in self.cache:
            self.cache[self.show_path] = self.create_diff_widgets(
                CMD.read(ReadCmd.diff_reverse, path_arg=self.show_path)
            )

        self.remove_children()
        self.mount_all(self.cache[self.show_path])
