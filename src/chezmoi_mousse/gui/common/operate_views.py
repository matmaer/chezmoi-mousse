from __future__ import annotations

from enum import StrEnum
from itertools import groupby
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual import work
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Collapsible, DataTable, Static

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.gui.common.components import FlatSectionLabel, SubSectionLabel
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
    from textual.widgets import Label

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["ContentView", "DiffReverseView", "DiffView", "GitLogView"]


class DirContentTitles(StrEnum):
    status_dirs = "Managed Directories (with status)"
    status_files = "Managed Files (with status)"
    managed_dirs = "Managed Directories (no status)"
    managed_files = "Managed Files (no status)"
    un_managed_dirs = "Directories (not managed)"
    un_managed_files = "Files (not managed)"
    un_wanted_dirs = "Directories (not managed, matches unwanted)"
    un_wanted_files = "Files (not managed, matches unwanted)"


class DirContensView(ScrollableContainer):
    def compose(self) -> ComposeResult:
        yield Collapsible(title=DirContentTitles.status_dirs)
        yield Collapsible(title=DirContentTitles.status_files)
        yield Collapsible(title=DirContentTitles.managed_dirs)
        yield Collapsible(title=DirContentTitles.managed_files)
        yield Collapsible(title=DirContentTitles.un_managed_dirs)
        yield Collapsible(title=DirContentTitles.un_managed_files)
        yield Collapsible(title=DirContentTitles.un_wanted_dirs)
        yield Collapsible(title=DirContentTitles.un_wanted_files)

    def update_collapsibles(self, dir_contents: dict[str, list[Path]]) -> None: ...


class ContentView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    path: reactive[Path | None] = reactive(None, init=False)

    txt_cache: ClassVar[dict[Path, Text]] = {}
    dir_content_cache: ClassVar[dict[Path, list[SubSectionLabel | Static]]] = {}

    class ContentStatic(Static): ...

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(LabelStr.select_path_contents)
        yield DirContensView()
        yield ContentView.ContentStatic(markup=False)

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.content_static = self.query_exactly_one(ContentView.ContentStatic)
        self.content_static.display = False
        self.dir_contents = self.query_exactly_one(ScrollableContainer)

    @work
    async def _create_dir_contents(self, path: Path) -> None:
        self.dir_contents.display = False
        self.dir_contents.remove_children()
        if path in self.dir_content_cache:
            widgets = self.dir_content_cache[path]
        else:
            widgets: list[SubSectionLabel | Static] = []
            status_files_in: list[Path] = path_funcs.get_nested_in(
                dir_path=path, check_paths=store.cm_paths.status_file_set
            )
            if status_files_in:
                widgets.append(SubSectionLabel(LabelStr.status_files_in))
                for path in status_files_in:
                    widgets.append(Static(str(path)))
                widgets.append(Static(""))  # add a spacer between sections

            status_dirs_in: list[Path] = path_funcs.get_nested_in(
                dir_path=path, check_paths=store.cm_paths.status_dir_set
            )
            if status_dirs_in:
                widgets.append(SubSectionLabel(LabelStr.status_dirs_in))
                for path in status_dirs_in:
                    widgets.append(Static(str(path)))
                widgets.append(Static(""))  # add a spacer between sections

            managed_dirs_in: list[Path] = path_funcs.get_nested_in(
                dir_path=path, check_paths=store.cm_paths.man_dir_set
            )
            if managed_dirs_in:
                widgets.append(SubSectionLabel(LabelStr.unchanged_dirs_in))
                for path in managed_dirs_in:
                    widgets.append(Static(str(path)))
                widgets.append(Static(""))  # add a spacer between sections

        self.dir_contents.mount_all(widgets)
        self.dir_contents.display = True

    @work
    async def _create_file_contents(self, path: Path) -> None:
        if path in self.txt_cache:
            f_content = self.txt_cache[path]
        else:
            f_content = Text("Looks like an empty file.")
            if path in store.cm_paths.missing_managed:
                f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                    self.app, path
                )
                self.flat_label.update(LabelStr.chezmoi_cat_output)
            else:
                self.flat_label.update(LabelStr.read_file_output)
                f_content = tchezmoi.get_highlighted_file_contents(path)
            self.txt_cache[path] = f_content

        self.content_static.update(f_content)

    def watch_path(self, path: Path) -> None:
        if path in store.cm_paths.un_wanted_plus_amp_dirs or path == store.cfg.dest_dir:
            self.flat_label.update(LabelStr.select_path_contents)
            self.content_static.display = False
            self.dir_contents.display = True
            self._create_dir_contents(path)
        elif path in store.cm_paths.un_wanted_plus_amp_files:
            self._create_file_contents(path)
        elif path not in store.cm_paths.path_labels:
            self.notify(f"missing path_labels for {path}")

        self.dir_contents.display = False
        self.content_static.display = True


class _DiffViewBase(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    path: reactive[Path | None] = reactive(None, init=False)

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
        yield ScrollableContainer()

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.diff_container = self.query_exactly_one(ScrollableContainer)
        self.diff_container.display = False

    async def _get_diff_widgets(self, diff_cmd: ReadCmd, path: Path) -> list[Static]:
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
    async def _update_diff_view(self, path: Path) -> None:

        self.flat_label.update(tchezmoi.pretty_cmd(self.diff_cmd, path))
        self.diff_container.display = True
        self.diff_container.loading = True

        if path in self.cache:
            self.diff_container.remove_children()
            self.diff_container.mount_all(self.cache[path])
        else:
            diff_statics = await self._get_diff_widgets(self.diff_cmd, path)
            self.cache[path] = diff_statics
            self.diff_container.mount_all(self.cache[path])
        self.diff_container.loading = False

    def watch_path(self, path: Path) -> None:
        if path in store.cm_paths.status_path_set:
            self._update_diff_view(path)
            return
        self.diff_container.display = False
        self.flat_label.update(LabelStr.select_path_diff)


class DiffView(_DiffViewBase):
    def __init__(self) -> None:
        super().__init__(ReadCmd.diff)


class DiffReverseView(_DiffViewBase):
    def __init__(self) -> None:
        super().__init__(ReadCmd.diff_reverse)


class GitLogView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    path: reactive[Path | None] = reactive(None, init=False)
    cache: ClassVar[dict[Path, list[list[str]]]] = {}

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel(ReadCmd.git_log.pretty_cmd)
        yield DataTable[str](show_cursor=False)

    def on_mount(self) -> None:
        self.flat_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")

    async def _get_styled_cells(self, log_lines: list[str]) -> list[list[str]]:
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
                stylize(columns, ColorVar.text_secondary)
            else:
                stylize(columns, ColorVar.text_primary)

        return pretty_cells

    @work
    async def _update_datatable(self, path: Path) -> None:
        self.data_table.clear()
        if path in self.cache:
            pretty_cells = self.cache[path]
        else:
            path_arg = None if path == store.cfg.dest_dir else path
            cmd_result = await tchezmoi.run_chezmoi_cmd(
                self.app, ReadCmd.git_log, path_arg
            )
            pretty_cells = await self._get_styled_cells(cmd_result.out_list)
            self.cache[path] = pretty_cells

        for row in pretty_cells:
            self.data_table.add_row(*row)
        self.data_table.display = True

    def watch_path(self, path: Path) -> None:
        if path != store.cfg.dest_dir and path not in store.cm_paths.man_path_set:
            self.data_table.display = False
            self.flat_label.update(LabelStr.select_path_git_log)
            return
        self._update_datatable(path)
