from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual import work
from textual.containers import (
    HorizontalGroup,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
)
from textual.reactive import reactive
from textual.widgets import DataTable, Label, Static

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.gui.common.components import FlatSectionLabel
from chezmoi_mousse.str_enums import (
    ColorVar,
    LabelStr,
    ReadCmd,
    StatusCode as Sc,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import NodeData


__all__ = ["ContentView", "DiffReverseView", "DiffView", "GitLogView"]


class TrueLabel(Label):
    def on_mount(self) -> None:
        self.update("yes")


class FalseLabel(Label):
    def on_mount(self) -> None:
        self.update(" no")


class PathInfo(ScrollableContainer):
    class DirInfo(VerticalGroup): ...

    class FileInfo(VerticalGroup): ...

    class InfoLabel(Label): ...

    class TrueLabel(Label): ...

    class FalseLabel(Label): ...

    class InfoItem(HorizontalGroup): ...

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield PathInfo.DirInfo()
        yield PathInfo.FileInfo()

    def on_mount(self) -> None:
        self.yes = "yes"
        self.no = "no"
        self.dir_info = self.query_exactly_one(PathInfo.DirInfo)
        self.file_info = self.query_exactly_one(PathInfo.FileInfo)
        self.file_info.display = False

    @work
    async def set_dir_info(self, node_data: NodeData) -> None:
        path = node_data.path
        status = node_data.status
        info_items: list[PathInfo.InfoItem] = []

        is_managed = TrueLabel() if path in store.cm_paths.man_dir_set else FalseLabel()
        has_status = (
            TrueLabel() if path in store.cm_paths.status_dir_set else FalseLabel()
        )
        has_nested_status = (
            TrueLabel()
            if path_funcs.any_nested_in(
                dir_path=path, check_paths=store.cm_paths.status_path_set
            )
            else FalseLabel()
        )
        has_nested_managed = (
            TrueLabel()
            if path_funcs.any_nested_in(
                dir_path=path, check_paths=store.cm_paths.man_path_set
            )
            else FalseLabel()
        )
        has_nested_unmanaged = TrueLabel() if status is Sc.YY else FalseLabel()
        has_nested_unwanted = TrueLabel() if node_data.status is Sc.XX else FalseLabel()
        manches_unwanted = TrueLabel() if status == Sc.XX else FalseLabel()
        exists = (
            TrueLabel() if path not in store.cm_paths.missing_managed else FalseLabel()
        )
        info_items.append(
            self.InfoItem(self.InfoLabel(LabelStr.d_is_managed), is_managed)
        )
        info_items.append(
            self.InfoItem(self.InfoLabel(LabelStr.d_has_status), has_status)
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.d_has_nested_status),
                has_nested_status,
            )
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.d_has_nested_managed),
                has_nested_managed,
            )
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.d_has_nested_un_man),
                has_nested_unmanaged,
            )
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.d_has_nested_un_wanted),
                has_nested_unwanted,
            )
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.d_match_un_wanted),
                manches_unwanted,
            )
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.d_exists),
                exists,
            )
        )

        self.dir_info.remove_children()
        self.dir_info.mount_all(info_items)

    @work
    async def set_file_info(self, node_data: NodeData) -> None:
        path = node_data.path
        status = node_data.status
        info_items: list[PathInfo.InfoItem] = []

        is_managed = (
            TrueLabel() if path in store.cm_paths.man_file_set else FalseLabel()
        )
        has_status = (
            TrueLabel() if path in store.cm_paths.status_file_set else FalseLabel()
        )
        f_match_unwanted = TrueLabel() if status is Sc.XX else FalseLabel()
        exists = (
            TrueLabel() if path not in store.cm_paths.missing_managed else FalseLabel()
        )

        info_items.append(
            self.InfoItem(self.InfoLabel(LabelStr.f_is_managed), is_managed)
        )
        info_items.append(
            self.InfoItem(self.InfoLabel(LabelStr.f_has_status), has_status)
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.f_match_un_wanted),
                f_match_unwanted,
            )
        )
        info_items.append(
            self.InfoItem(
                self.InfoLabel(LabelStr.f_exists),
                exists,
            )
        )

        self.file_info.remove_children()
        self.file_info.mount_all(info_items)

    def watch_node_data(self, node_data: NodeData) -> None:
        path = node_data.path
        if path in store.cm_paths.file_node_data or path.is_file():
            self.dir_info.display = False
            self.set_file_info(node_data)
            self.file_info.display = True
        else:
            self.file_info.display = False
            self.set_dir_info(node_data)
            self.dir_info.display = True


class ContentView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    file_content_cache: ClassVar[dict[Path, Text]] = {}

    class FileContentStatic(Static): ...

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.select_path_contents)
        yield self.FileContentStatic(markup=False)
        yield PathInfo()

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.content_static = self.query_exactly_one(ContentView.FileContentStatic)
        self.content_static.display = False
        self.path_info = self.query_exactly_one(PathInfo)

    @work
    async def _update_file_content(self, path: Path) -> None:
        if path in self.file_content_cache:
            f_content = self.file_content_cache[path]
        else:
            f_content = Text("Looks like an empty file.")
            if path in store.cm_paths.missing_managed:
                f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                    self.app, path
                )
                self.flat_label.update(tchezmoi.pretty_cmd(ReadCmd.cat, path))
            else:
                self.flat_label.update(LabelStr.read_file_output)
                f_content = tchezmoi.get_highlighted_file_contents(path)
            self.file_content_cache[path] = f_content
        self.content_static.update(f_content)

    def watch_node_data(self, node_data: NodeData) -> None:
        path = node_data.path
        if path in store.cm_paths.file_node_data or path.is_file():
            self.path_info.display = False
            self._update_file_content(path)
            self.content_static.display = True
        else:
            self.content_static.display = False
            self.flat_label.update(LabelStr.select_path_contents)
            self.path_info.node_data = node_data
            self.path_info.display = True


class _DiffViewBase(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    class DiffWidgets(ScrollableContainer): ...

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    cache: ClassVar[dict[Path, list[Static]]] = {}

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
        super().__init__()

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.select_path_diff)
        yield self.DiffWidgets()
        yield PathInfo()

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.diff_container = self.query_exactly_one(_DiffViewBase.DiffWidgets)
        self.diff_container.display = False
        self.path_info = self.query_exactly_one(PathInfo)

    async def _create_diff_widgets(self, diff_cmd: ReadCmd, path: Path) -> list[Static]:
        diff_result = await tchezmoi.run_chezmoi_cmd(self.app, diff_cmd, path)
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
                        Static(line, classes=self.tcss_map[prefix].value, markup=False)
                    )
        return widgets

    @work
    async def _update_diff_view(self, node_data: NodeData) -> None:

        if node_data.path in self.cache:
            diff_widgets = self.cache[node_data.path]
        else:
            diff_widgets = await self._create_diff_widgets(
                self.diff_cmd, node_data.path
            )
            self.cache[node_data.path] = diff_widgets

        self.diff_container.remove_children()
        self.diff_container.mount_all(diff_widgets)

    def watch_node_data(self, node_data: NodeData) -> None:
        if node_data.path not in store.cm_paths.status_path_set:
            self.flat_label.update(LabelStr.select_path_diff)
            self.diff_container.display = False
            self.path_info.node_data = node_data
            self.path_info.display = True
        else:
            self.path_info.display = False
            self.flat_label.update(tchezmoi.pretty_cmd(self.diff_cmd, node_data.path))
            self.diff_container.loading = True
            self.diff_container.display = True
            self._update_diff_view(node_data)
            self.diff_container.loading = False


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
        yield FlatSectionLabel(ReadCmd.git_log.pretty_cmd)
        yield DataTable[str](show_cursor=False)
        yield PathInfo()

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")
        self.path_info = self.query_exactly_one(PathInfo)
        self.path_info.display = False

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
    async def _update_datatable_and_flat_label(self, path: Path) -> None:
        self.data_table.clear()
        if path in self.cache:
            self.flat_label.update(tchezmoi.pretty_cmd(ReadCmd.git_log, path))
            pretty_cells = self.cache[path]
        else:
            path_arg = None if path == store.cfg.dest_dir else path
            cmd_result = await tchezmoi.run_chezmoi_cmd(
                self.app, ReadCmd.git_log, path_arg
            )
            self.flat_label.update(cmd_result.pretty_cmd)
            pretty_cells = self._get_styled_cells(cmd_result.out_list)
            self.cache[path] = pretty_cells

        for row in pretty_cells:
            self.data_table.add_row(*row)
        self.data_table.display = True

    def watch_node_data(self, node_data: NodeData) -> None:
        path = node_data.path
        if path != store.cfg.dest_dir and path not in store.cm_paths.man_path_set:
            self.data_table.display = False
            self.flat_label.update(LabelStr.select_path_git_log)
            self.path_info.display = True
            self.path_info.node_data = node_data
            return
        self._update_datatable_and_flat_label(path)
