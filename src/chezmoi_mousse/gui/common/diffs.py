from itertools import groupby
from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import CMD, AppIds, AppType, ReadCmd, TabName, Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import DirNode


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


class DiffView(Container, AppType):

    show_path: reactive["Path"] = reactive(CMD.dest_dir)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff)
        self.ids = ids
        self.cache: dict[Path, ScrollableContainer] = {}
        self.current_container: ScrollableContainer = ScrollableContainer()

    @property
    def dir_nodes(self) -> dict["Path", "DirNode"]:
        if self.ids.canvas_name == TabName.apply:
            return CMD.apply_dir_nodes
        else:
            return CMD.re_add_dir_nodes

    def _create_diff_widgets(self) -> list[Label | Static]:
        widgets: list[Label | Static] = []
        if self.ids.canvas_name == TabName.apply:
            diff_result = CMD.run_cmd.read(ReadCmd.diff, path_arg=self.show_path)
        else:  # re-add tab
            diff_result = CMD.run_cmd.read(
                ReadCmd.diff_reverse, path_arg=self.show_path
            )
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

    def _mount_and_cache_container(
        self, path: "Path", widgets: list[Label | Static]
    ) -> None:
        self.current_container.display = False
        container = ScrollableContainer()
        self.mount(container)
        container.mount_all(widgets)
        self.cache[path] = container
        self.current_container = container

    def watch_show_path(self, show_path: "Path") -> None:
        if show_path in self.cache:
            self.current_container.display = False
            self.cache[show_path].display = True
            self.current_container = self.cache[show_path]
            return
        widgets: list[Label | Static] = []
        if show_path in CMD.status_paths:
            widgets = self._create_diff_widgets()
        elif show_path in CMD.managed_dirs:
            widgets = self.dir_nodes[show_path].dir_widgets
        elif show_path in CMD.managed_files:
            widgets.append(Label("Managed file", classes=Tcss.main_section_label))
            widgets.append(Label(str(show_path), classes=Tcss.sub_section_label))
            widgets.append(Static("This file has no status.", classes=Tcss.context))
        else:
            widgets.append(Static("Nothing to show."))
        self._mount_and_cache_container(show_path, widgets)
