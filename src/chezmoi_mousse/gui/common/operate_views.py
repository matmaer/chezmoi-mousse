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


__all__ = ["ContentView", "DiffReverseView", "DiffView", "GitLogView", "PathView"]


class TrueLabel(Label):
    def on_mount(self) -> None:
        self.update("yes")


class FalseLabel(Label):
    def on_mount(self) -> None:
        self.update(" no")


class FileContentStatic(Static): ...


class ContentView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_data: reactive[NodeData | None] = reactive(None, init=False)

    cache: ClassVar[dict[Path, Text]] = {}

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.not_set)
        yield ScrollableContainer(FileContentStatic(markup=False))

    def on_mount(self) -> None:
        self.last_displayed_path: Path | None = None
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.content_static = self.query_exactly_one(FileContentStatic)

    @work
    async def _update_file_content(self, node_data: NodeData) -> None:
        path = node_data.path
        if path in self.cache:
            f_content = self.cache[path]
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
            self.cache[path] = f_content
        self.content_static.update(f_content)

    def watch_node_data(self, node_data: NodeData) -> None:
        assert node_data.file_path, "ContentView requires a file path"
        if node_data.path == self.last_displayed_path:
            return

        self._update_file_content(node_data)
        self.last_displayed_path = node_data.path


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
        self.last_displayed_path: Path | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.not_set)
        yield DiffWidgets()

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.diff_container = self.query_exactly_one(DiffWidgets)

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
        assert node_data.has_status, "NodeData must have a status"
        if node_data.path == self.last_displayed_path:
            return

        self.flat_label.update(tchezmoi.pretty_cmd(self.diff_cmd, node_data.path))
        self._create_diff_widgets(self.diff_cmd, node_data.path)
        self.last_displayed_path = node_data.path


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
        self.last_displayed_path: Path | None = None
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")

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
    async def update_git_log_view(
        self, path: Path, log_lines: list[str] | None = None
    ) -> None:
        pretty_cells = []
        if path == self.last_displayed_path:
            return
        if path in self.cache:
            pretty_cells = self.cache[path]
        elif log_lines is not None:
            pretty_cells = self._get_styled_cells(log_lines)
            self.cache[path] = pretty_cells

        flat_label = tchezmoi.pretty_cmd(ReadCmd.git_log, path)
        self.flat_label.update(flat_label)
        self.last_displayed_path = path

        self.data_table.clear()
        for row in pretty_cells:
            self.data_table.add_row(*row)


class PathView(Vertical):
    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.select_path_git_log)
        yield SubSectionLabel(str(store.cm_paths.dest_dir_node_data.path))
        yield PathInfo()

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.sub_label = self.query_exactly_one(SubSectionLabel)
        self.path_info = self.query_exactly_one(PathInfo)
