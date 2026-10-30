from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from rich.markup import escape
from textual import work
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from chezmoi_mousse import tchezmoi
from chezmoi_mousse.gui.common import widget_factory
from chezmoi_mousse.gui.common.components import FlatSectionLabel
from chezmoi_mousse.str_enums import ColorVar, LabelStr, ReadCmd

if TYPE_CHECKING:
    from pathlib import Path

    from rich.text import Text
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["ContentView", "DiffReverseView", "DiffView", "GitLogView", "PathView"]


class ContentView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    cache: ClassVar[dict[Path, Text]] = {}

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.not_set)
        yield ScrollableContainer(Static(markup=False))

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        scrollable_container = self.query_exactly_one(ScrollableContainer)
        self.content_static = scrollable_container.query_exactly_one(Static)

    @work
    async def _update_file_content(self, node_data: NodeData) -> None:
        path = node_data.path
        if path in self.cache:
            f_content = self.cache[path]
        else:
            if not node_data.exists:
                f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                    self.app, file_path=path
                )
                self.flat_label.update(escape(tchezmoi.pretty_cmd(ReadCmd.cat, path)))
            else:
                self.flat_label.update(LabelStr.read_file_output)
                f_content = tchezmoi.get_highlighted_file_contents(path)
            self.cache[path] = f_content
        self.content_static.update(f_content)

    def watch_node_data(self, node_data: NodeData) -> None:
        assert node_data.file_path, "ContentView requires a file path"
        self._update_file_content(node_data)


class _DiffViewBase(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    def __init__(self, diff_cmd: ReadCmd) -> None:
        self.diff_cmd = diff_cmd
        self.cache: dict[Path, list[Static]] = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        yield ScrollableContainer()

    def on_mount(self) -> None:
        self.diff_container = self.query_exactly_one(ScrollableContainer)

    @work
    async def _create_diff_widgets(self, diff_cmd: ReadCmd, path: Path) -> None:
        if path not in self.cache:
            diff_result = await tchezmoi.run_chezmoi_cmd(
                self.app, diff_cmd, verb_arg=path
            )
            self.cache[path] = widget_factory.diff_lines(diff_result.std_out)

        self.diff_container.remove_children()
        self.diff_container.mount_all(self.cache[path])

    def watch_node_data(self, node_data: NodeData) -> None:
        self._create_diff_widgets(self.diff_cmd, node_data.path)


class DiffView(_DiffViewBase):
    def __init__(self) -> None:
        super().__init__(ReadCmd.diff)


class DiffReverseView(_DiffViewBase):
    def __init__(self) -> None:
        super().__init__(ReadCmd.diff_reverse)


class GitLogView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cache: ClassVar[dict[Path, list[list[str]]]] = {}

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel()
        yield DataTable[str](show_cursor=False)

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")

    def _get_styled_cells(self, std_out: str) -> list[list[str]]:
        pretty_cells: list[list[str]] = []

        def stylize(columns: list[str], log_color: ColorVar) -> list[str]:
            color = self.app.theme_variables[log_color]
            row: list[str] = [
                f"[{color}]{escape(cell_text)}[/]" for cell_text in columns
            ]
            return row

        # Split on the NUL record terminator only: str.splitlines() also splits
        # on characters like \x1c-\x1e, \x85 and \u2028 if found in commit text!
        for line in std_out.split("\x00"):
            line = line.lstrip("\r\n")
            if not line:
                continue
            no_commit_message = "no commit message"
            rel_date, committer, message = line.split("\x1f", 2)
            column_one = f"{rel_date} by {committer}"
            column_two = message if message.strip() else no_commit_message
            columns: list[str] = [column_one, column_two]
            if column_two.split(maxsplit=1)[0] == "Add":
                row = stylize(columns, ColorVar.text_success)
            elif column_two.split(maxsplit=1)[0] == "Update":
                row = stylize(columns, ColorVar.text_warning)
            elif column_two.split(maxsplit=1)[0] == "Remove":
                row = stylize(columns, ColorVar.text_error)
            elif column_two == no_commit_message:
                row = stylize(columns, ColorVar.secondary)
            else:
                row = stylize(columns, ColorVar.text_primary)
            pretty_cells.append(row)

        return pretty_cells

    @work
    async def update_git_log_view(
        self, node_data: NodeData, std_out: str | None = None
    ) -> None:
        assert node_data.managed or node_data.dir_data.dest_dir
        if node_data.path in self.cache or std_out is None:
            pretty_cells = self.cache[node_data.path]
        else:
            pretty_cells = self._get_styled_cells(std_out)
            self.cache[node_data.path] = pretty_cells

        label_path = node_data.path if not node_data.dir_data.dest_dir else None
        flat_label = tchezmoi.pretty_cmd(ReadCmd.git_log, label_path)
        self.flat_label.update(escape(flat_label))

        self.data_table.clear()
        for row in pretty_cells:
            self.data_table.add_row(*row, height=None)


class PathView(ScrollableContainer):
    node_data: reactive[NodeData | None] = reactive(None, init=False)

    @work
    async def _set_path_info(self, n_data: NodeData) -> None:
        truth_dict: dict[str, bool] = {}
        truth_dict[LabelStr.path_has_status] = n_data.status_path
        truth_dict[LabelStr.path_exists] = n_data.exists
        truth_dict[LabelStr.path_un_wanted] = (
            n_data.wanted is False and not n_data.managed
        )
        if n_data.dir_path or n_data.path.is_dir():
            truth_dict[LabelStr.has_nested_status] = n_data.dir_data.nested_status
            truth_dict[LabelStr.has_nested_managed] = n_data.dir_data.nested_managed
            truth_dict[LabelStr.has_nested_un_man] = n_data.dir_data.nested_un_managed
            truth_dict[LabelStr.has_child_paths] = n_data.dir_data.has_child_paths
        self.remove_children()
        self.mount_all(widget_factory.truth_widgets(truth_dict))

    def watch_node_data(self, node_data: NodeData) -> None:
        self._set_path_info(node_data)
