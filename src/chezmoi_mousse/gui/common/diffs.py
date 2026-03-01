from itertools import groupby
from pathlib import Path

from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import CMD, AppIds, AppType, DirNode, ReadCmd, TabName, Tcss

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

    def _create_diff_widgets(self) -> list[Label | Static]:
        widgets: list[Label | Static] = []
        if self.show_path not in CMD.status_paths:
            if self.show_path in CMD.managed_dirs:
                return [
                    Label("Managed directory", classes=Tcss.main_section_label),
                    Label(str(self.show_path), classes=Tcss.sub_section_label),
                    Static(
                        "The directory has no chezmoi status and contains no nested "
                        "paths with a status.",
                        classes=Tcss.info,
                    ),
                ]
            elif self.show_path in CMD.managed_files:
                return [
                    Label("Managed file", classes=Tcss.main_section_label),
                    Label(str(self.show_path), classes=Tcss.sub_section_label),
                    Static("The file has no chezmoi status.", classes=Tcss.info),
                ]
        if self.canvas_name == TabName.apply:
            diff_result = CMD.run_cmd.read(ReadCmd.diff, path_arg=self.show_path)
        elif self.canvas_name == TabName.re_add:
            diff_result = CMD.run_cmd.read(
                ReadCmd.diff_reverse, path_arg=self.show_path
            )
        else:
            raise ValueError(f"Unexpected canvas name: {self.canvas_name}")
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

    def _mount_new_container(self, path: Path, *widgets: Static) -> None:
        if self.current_container is not None:
            self.current_container.display = False
        container = ScrollableContainer()
        self.mount(container)
        container.mount_all(widgets)
        self.cache[path] = container
        self.current_container = container

    def _toggle_display_cached_container(self, path: Path) -> None:
        # Hide current container, show the selected one
        if self.current_container is not None:
            self.current_container.display = False
        self.cache[path].display = True
        self.current_container = self.cache[path]
        if self.show_path == CMD.dest_dir:
            self.border_title = f" {CMD.dest_dir} "
        else:
            self.border_title = f" {path.name} "

    def watch_show_path(self) -> None:
        if self.show_path is None:
            widgets = self.dir_nodes[CMD.dest_dir].dir_widgets
            self._mount_new_container(CMD.dest_dir, *widgets)
            return
        elif self.show_path in self.cache:
            self._toggle_display_cached_container(self.show_path)
            return
        widgets = self._create_diff_widgets()
        self._mount_new_container(self.show_path, *widgets)
        self.border_title = f" {self.show_path.name} "
