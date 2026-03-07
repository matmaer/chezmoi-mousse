from itertools import groupby
from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import CMD, AppIds, AppType, ReadCmd, TabLabel, Tcss

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

    show_path: reactive["Path | None"] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff)
        self.ids = ids
        self.container_cache: dict[Path, ScrollableContainer] = {}
        self.current_container_path: Path | None = None

    def on_mount(self) -> None:
        self.show_path = CMD.cache.dest_dir

    @property
    def dir_nodes(self) -> dict["Path", "DirNode"]:
        if self.ids.canvas_name == TabLabel.apply:
            return CMD.cache.apply_dir_nodes
        else:
            return CMD.cache.re_add_dir_nodes

    def _create_diff_widgets(self) -> list[Label | Static]:
        widgets: list[Label | Static] = []
        if self.ids.canvas_name == TabLabel.apply:
            diff_result = CMD.run_cmd.read(ReadCmd.diff, path_arg=self.show_path)
        else:  # re-add tab
            diff_result = CMD.run_cmd.read(
                ReadCmd.diff_reverse, path_arg=self.show_path
            )
        self.app.log_cmd_result(diff_result)
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
        self.container_cache[path] = ScrollableContainer(*widgets)
        self.mount(self.container_cache[path])
        self.current_container_path = path

    def update_mounted_containers(self, changed_paths: list["Path"]) -> None:
        for path, container in self.container_cache.items():
            if path in changed_paths:
                container.remove()
        self.show_path = CMD.cache.dest_dir

    def watch_show_path(self, show_path: "Path | None") -> None:
        if show_path is None:
            return

        # Hide the previously displayed container
        if self.current_container_path is not None:
            previous_container = self.container_cache.get(
                self.current_container_path, None
            )
            if previous_container is not None:
                previous_container.display = False

        is_mounted = show_path in self.container_cache
        if is_mounted and self.current_container_path is not None:
            self.container_cache[show_path].display = True
            self.current_container_path = show_path
            return

        widgets: list[Label | Static] = []
        if show_path in CMD.cache.status_paths:
            widgets = self._create_diff_widgets()
        elif show_path in CMD.cache.managed_dirs_with_dest_dir:
            widgets = self.dir_nodes[show_path].dir_widgets
        elif show_path in CMD.cache.managed_file_paths:
            widgets.append(Label("Managed file", classes=Tcss.main_section_label))
            widgets.append(Label(str(show_path), classes=Tcss.sub_section_label))
            widgets.append(Static("This file has no status.", classes=Tcss.context))
        else:
            widgets.append(Static("Nothing to show."))
        self._mount_and_cache_container(show_path, widgets)
