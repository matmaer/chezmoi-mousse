from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual import work
from textual.containers import (
    ScrollableContainer,
    Vertical,
)
from textual.reactive import reactive
from textual.widgets import DataTable, Label, Static

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    PathInfo,
    SubSectionLabel,
)
from chezmoi_mousse.str_enums import (
    ColorVar,
    LabelStr,
    ReadCmd,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["ContentView", "DiffReverseView", "DiffView", "GitLogView"]


class TrueLabel(Label):
    def on_mount(self) -> None:
        self.update("yes")


class FalseLabel(Label):
    def on_mount(self) -> None:
        self.update(" no")


class FileContentStatic(Static): ...


class ViewVertical(Vertical): ...


class PathInfoVertical(Vertical): ...


class ContentView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    file_content_cache: ClassVar[dict[Path, Text]] = {}

    def compose(self) -> ComposeResult:
        with ViewVertical():
            yield FlatSectionLabel(LabelStr.not_set)
            yield ScrollableContainer(FileContentStatic(markup=False))
        with PathInfoVertical():
            yield SubSectionLabel(LabelStr.select_path_contents)
            yield PathInfo()

    def on_mount(self) -> None:
        self.view_vertical = self.query_exactly_one(ViewVertical)
        self.view_vertical.display = False
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.content_static = self.query_exactly_one(FileContentStatic)

        self.path_info_vertical = self.query_exactly_one(PathInfoVertical)
        self.path_info = self.path_info_vertical.query_exactly_one(PathInfo)

    @work
    async def _update_file_content(self, node_data: NodeData) -> None:
        path = node_data.path
        if path in self.file_content_cache:
            f_content = self.file_content_cache[path]
        else:
            f_content = Text("Looks like an empty file.")
            if not node_data.exists:
                f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                    self.app, file_path=path
                )
                self.flat_label.update(tchezmoi.pretty_cmd(ReadCmd.cat, path))
            else:
                self.flat_label.update(LabelStr.read_file_output)
                f_content = tchezmoi.get_highlighted_file_contents(path)
            self.file_content_cache[path] = f_content
        self.content_static.update(f_content)

    def watch_node_data(self, node_data: NodeData) -> None:
        self.path_info.node_data = node_data
        if node_data.dir_path or node_data.path.is_dir():
            self.view_vertical.display = False
            self.path_info_vertical.display = True
        else:
            self.path_info_vertical.display = False
            self._update_file_content(node_data)
            self.view_vertical.display = True


class DiffWidgets(ScrollableContainer): ...


class _DiffViewBase(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    tcss_map: ClassVar[dict[str, Tcss]] = {
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

    def __init__(self, diff_cmd: ReadCmd) -> None:
        self.diff_cmd = diff_cmd
        self.cache: dict[Path, list[Static]] = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        with ViewVertical():
            yield FlatSectionLabel(LabelStr.not_set)
            yield ScrollableContainer(DiffWidgets())
        with PathInfoVertical():
            yield SubSectionLabel(LabelStr.select_path_diff)
            yield PathInfo()

    def on_mount(self) -> None:
        self.view_vertical = self.query_exactly_one(ViewVertical)
        self.view_vertical.display = False
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.diff_container = self.query_exactly_one(DiffWidgets)

        self.path_info_vertical = self.query_exactly_one(PathInfoVertical)
        self.path_info = self.path_info_vertical.query_exactly_one(PathInfo)

    @work
    async def _create_diff_widgets(self, diff_cmd: ReadCmd, path: Path) -> None:

        if path in self.cache:
            widgets = self.cache[path]

        else:
            diff_result = await tchezmoi.run_chezmoi_cmd(
                self.app, diff_cmd, verb_arg=path
            )
            widgets: list[Label | Static] = []

            def get_prefix(line: str) -> str:
                for p in self.tcss_map:
                    if line.startswith(p):
                        return p
                return " "

            for prefix, group_lines in groupby(diff_result.out_list, key=get_prefix):
                group_list = list(group_lines)
                if prefix in ("+", "-"):
                    text = "\n".join(group_list)
                    widgets.append(
                        Static(text, classes=self.tcss_map[prefix].value, markup=False)
                    )
                else:
                    for line in group_list:
                        widgets.append(
                            Static(
                                line, classes=self.tcss_map[prefix].value, markup=False
                            )
                        )
            self.cache[path] = widgets

        self.diff_container.remove_children()
        self.diff_container.mount_all(widgets)

    def watch_node_data(self, node_data: NodeData) -> None:
        self.path_info.node_data = node_data
        if node_data.has_status:
            self.path_info_vertical.display = False
            self.flat_label.update(tchezmoi.pretty_cmd(self.diff_cmd, node_data.path))
            self._create_diff_widgets(self.diff_cmd, node_data.path)
            self.view_vertical.display = True
        else:
            self.view_vertical.display = False
            self.path_info_vertical.display = True


class DiffView(_DiffViewBase):
    def __init__(self) -> None:
        super().__init__(ReadCmd.diff)


class DiffReverseView(_DiffViewBase):
    def __init__(self) -> None:
        super().__init__(ReadCmd.diff_reverse)


class GitLogView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)
    cache: ClassVar[dict[Path, list[list[str]]]] = {}

    def compose(self) -> ComposeResult:
        with ViewVertical():
            yield FlatSectionLabel(ReadCmd.git_log.pretty_cmd)
            yield DataTable[str](show_cursor=False)
        with PathInfoVertical():
            yield SubSectionLabel(LabelStr.no_git_log)
            yield PathInfo()

    def on_mount(self) -> None:
        self.view_vertical = self.query_exactly_one(ViewVertical)
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")
        self.path_info_vertical = self.query_exactly_one(PathInfoVertical)
        self.path_info = self.path_info_vertical.query_exactly_one(PathInfo)

    def _get_styled_cells(self, log_lines: list[str]) -> list[list[str]]:
        pretty_cells: list[list[str]] = []

        def stylize(columns: list[str], log_color: ColorVar) -> None:
            color = self.app.theme_variables[log_color]
            row: list[str] = [f"[{color}]{cell_text}[/]" for cell_text in columns]
            pretty_cells.append(row)

        for line in log_lines:
            no_commit_message = "no commit message"
            rel_date, committer, subject = line.rstrip("\x00").split("\x1f", 2)
            column_one = f"{rel_date} by {committer}"
            column_two = f"{subject}" if subject.strip() else no_commit_message
            columns: list[str] = [column_one, column_two]
            if column_two.split(maxsplit=1)[0] == "Add":
                stylize(columns, ColorVar.text_success)
            elif column_two.split(maxsplit=1)[0] == "Update":
                stylize(columns, ColorVar.text_warning)
            elif column_two.split(maxsplit=1)[0] == "Remove":
                stylize(columns, ColorVar.text_error)
            elif column_two == no_commit_message:
                stylize(columns, ColorVar.secondary)
            else:
                stylize(columns, ColorVar.text_primary)

        return pretty_cells

    @work
    async def _update_datatable_and_flat_label(self, node_data: NodeData) -> bool:
        source_path = node_data.source_path
        path = source_path if source_path is not None else store.cfg.dest_dir
        self.data_table.clear()
        if path in self.cache:
            self.flat_label.update(tchezmoi.pretty_cmd(ReadCmd.git_log, path))
            pretty_cells = self.cache[path]
        else:
            path_arg = None if path == store.cfg.dest_dir else path
            cmd_result = await tchezmoi.run_chezmoi_cmd(
                self.app, ReadCmd.git_log, path_arg=path_arg
            )
            self.flat_label.update(cmd_result.pretty_cmd)
            pretty_cells = self._get_styled_cells(cmd_result.out_list)

        if not pretty_cells:
            return False

        for row in pretty_cells:
            self.data_table.add_row(*row)
        self.cache[path] = pretty_cells
        return True

    def watch_node_data(self, node_data: NodeData) -> None:
        self.path_info.node_data = node_data
        if node_data.path == store.cfg.dest_dir or node_data.managed:
            has_data = self._update_datatable_and_flat_label(node_data)
            if has_data:
                self.path_info_vertical.display = False
                self.view_vertical.display = True
            else:
                self.view_vertical.display = False
                self.path_info_vertical.display = True
        else:
            self.flat_label.update(LabelStr.select_path_git_log)
            self.path_info_vertical.display = True
            self.view_vertical.display = False
