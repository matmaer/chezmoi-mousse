from itertools import groupby
from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import CMD, AppIds, AppType, ReadCmd, TabLabel, Tcss

from .messages import LogCmdResultMsg

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

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff)
        self.ids = ids
        self.mounted: dict[Path, str] = {}
        self.current_path: Path | None = None

    def hide_all_containers(self) -> None:
        for container in self.query_children(ScrollableContainer):
            container.display = False

    @property
    def dir_nodes(self) -> dict["Path", "DirNode"]:
        if self.ids.canvas_name == TabLabel.apply:
            return CMD.cache.apply_dir_nodes
        else:
            return CMD.cache.re_add_dir_nodes

    def _create_diff_widgets(self, path: "Path") -> list[Label | Static]:
        widgets: list[Label | Static] = []
        if self.ids.canvas_name == TabLabel.apply:
            diff_result = CMD.run_cmd.read(ReadCmd.diff, path_arg=path)
        else:  # re-add tab
            diff_result = CMD.run_cmd.read(ReadCmd.diff_reverse, path_arg=path)
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

    def watch_show_path(self, show_path: "Path | None") -> None:
        if show_path is None:
            return
        self.hide_all_containers()
        sc_id = self.app.path_to_id(show_path)
        sc_id_q = self.app.path_to_qid(show_path)
        try:
            container = self.query_one(sc_id_q, ScrollableContainer)
            container.display = True
        except NoMatches:
            widgets: list[Label | Static] = []
            if show_path == CMD.cache.dest_dir:
                widgets = self.dir_nodes[show_path].dir_widgets
            elif show_path in CMD.cache.managed_dir_paths:
                if show_path in CMD.cache.status_paths:
                    widgets = self._create_diff_widgets(show_path)
                else:
                    widgets = self.dir_nodes[show_path].dir_widgets
            elif show_path in CMD.cache.managed_file_paths:
                if show_path in CMD.cache.status_paths:
                    widgets = self._create_diff_widgets(show_path)
                else:
                    widgets.append(
                        Label("Managed file", classes=Tcss.main_section_label)
                    )
                    widgets.append(
                        Label(str(show_path), classes=Tcss.sub_section_label)
                    )
                    widgets.append(
                        Static("This file has no status.", classes=Tcss.context)
                    )
            else:
                widgets.append(Static("Nothing to show."))
            container = ScrollableContainer(*widgets, id=sc_id)
            self.mount(container)
            self.mounted[show_path] = sc_id

        self.current_path = show_path
