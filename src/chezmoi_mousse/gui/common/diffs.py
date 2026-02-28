from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Static

from chezmoi_mousse import (
    CMD,
    AppIds,
    AppType,
    DirNode,
    OperateString,
    ReadCmd,
    TabName,
    Tcss,
)

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

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

    show_path: reactive["Path | None"] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff, classes=Tcss.border_title_top)
        self.cache: dict[Path, ScrollableContainer] = {}
        self.canvas_name = ids.canvas_name
        self.current_container: ScrollableContainer | None = None

    def on_mount(self) -> None:
        self.border_title = f" {CMD.dest_dir} "

    @property
    def dir_nodes(self) -> dict[Path, "DirNode"]:
        if self.canvas_name == TabName.apply:
            return CMD.apply_dir_nodes
        else:
            return CMD.re_add_dir_nodes

    def _create_diff_widgets(self, diff_result: "CommandResult") -> list[Static]:
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
                widgets.append(
                    Static(text, classes=DIFF_TCSS[prefix].value, markup=False)
                )
            else:
                for line in group_list:
                    widgets.append(
                        Static(line, classes=DIFF_TCSS[prefix].value, markup=False)
                    )
        return widgets

    def _cache_container(self, path: Path, *widgets: Static) -> ScrollableContainer:
        container = ScrollableContainer()
        self.mount(container)
        container.mount_all(widgets)
        self.cache[path] = container
        return container

    def watch_show_path(self) -> None:
        if self.show_path is None:
            self.show_path = CMD.dest_dir
            widgets: list[Static] = self.dir_nodes[self.show_path].dir_widgets
            if widgets:
                container = self._cache_container(self.show_path, *widgets)
                self.mount(container)
                self.cache[self.show_path] = container
                return

            if not CMD.managed_dirs and not CMD.managed_files:
                widgets.append(
                    Static(
                        "No managed paths or paths with a status are in the chezmoi "
                        "repository.",
                        classes=Tcss.added,
                        markup=False,
                    )
                )
                widgets.append(
                    Static(
                        "Switch to the Add tab to add paths.",
                        classes=Tcss.added,
                        markup=False,
                    )
                )
            elif CMD.no_status_paths is True:
                text = (
                    "No diffs are available because no paths are present in the chezmoi"
                    "status output.\n<- Select an unchanged path to view its contents."
                    "in the Contents tab or the git log in the Git-Log tab."
                )
                widgets.append(Static(text, classes=Tcss.added, markup=False))
            else:
                text = (
                    "This is the destination directory, it has no diff output.\n"
                    "<- Select a file or directory in the tree to view its diff."
                )
                widgets.append(Static(text, classes=Tcss.added, markup=False))
            self._cache_container(Path(CMD.dest_dir), *widgets)

        elif self.show_path not in self.cache:
            if self.canvas_name == TabName.apply:
                diff_result = CMD.run_cmd.read(ReadCmd.diff, path_arg=self.show_path)
            elif self.canvas_name == TabName.re_add:
                diff_result = CMD.run_cmd.read(
                    ReadCmd.diff_reverse, path_arg=self.show_path
                )
            else:
                raise ValueError(f"Unexpected canvas name: {self.canvas_name}")
            if not diff_result.std_out and self.show_path in CMD.managed_files:
                widgets = [Static(OperateString.file_no_diff)]
            elif not diff_result.std_out and self.show_path in CMD.managed_dirs:
                widgets = self.dir_nodes[self.show_path].dir_widgets
                container = self._cache_container(self.show_path, *widgets)
                self.mount(container)
                self.cache[self.show_path] = container
            else:
                widgets = self._create_diff_widgets(diff_result)
            self._cache_container(self.show_path, *widgets)
        if self.show_path != CMD.dest_dir:
            self.border_title = f" {self.show_path.name} "
        # Hide current container, show the selected one
        if self.current_container is not None:
            self.current_container.display = False
        self.cache[self.show_path].display = True
        self.current_container = self.cache[self.show_path]
