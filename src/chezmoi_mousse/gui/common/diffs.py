from itertools import groupby
from pathlib import Path

from textual.containers import Container, ScrollableContainer
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


class DiffView(Container, AppType):

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff, classes=Tcss.border_title_top)
        self.cache: dict[Path, ScrollableContainer] = {}
        self.canvas_name = ids.canvas_name
        self.current_container: ScrollableContainer | None = None

    def on_mount(self) -> None:
        self.border_title = f" {self.app.parsed.dest_dir} "

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

    def _cache_container(self, path: Path, *widgets: Static) -> ScrollableContainer:
        """Helper to mount and cache a ScrollableContainer with widgets."""
        container = ScrollableContainer()
        self.mount(container)
        container.mount_all(widgets)
        self.cache[path] = container
        return container

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return

        if self.show_path not in self.cache:
            # Determine which diff command to use
            if self.canvas_name == TabName.apply:
                diff_result = CMD.read(ReadCmd.diff, path_arg=self.show_path)
            elif self.canvas_name == TabName.re_add:
                diff_result = CMD.read(ReadCmd.diff_reverse, path_arg=self.show_path)
            else:
                return

            widgets = self.create_diff_widgets(diff_result)
            self._cache_container(self.show_path, *widgets)

        # Hide current container, show the selected one
        if self.current_container is not None:
            self.current_container.display = False
        self.cache[self.show_path].display = True
        self.current_container = self.cache[self.show_path]
