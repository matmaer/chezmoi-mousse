from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING, ClassVar

from rich.text import Text
from textual import work
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    MainSectionLabel,
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
    from textual.widgets import Label

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["DiffReverseView", "DiffView", "GitLogView", "OperateViews"]


# Base view class ONLY for reactive path state (No compose, no extra DOM)
class BaseView(Vertical):
    path: reactive[Path | None] = reactive(None, init=False)

    def watch_path(self, path: Path | None) -> None:
        if path is not None:
            self.on_path_changed(path)

    def on_path_changed(self, path: Path) -> None:
        """Override in child views to react to path updates."""
        pass


class ContentView(BaseView):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cache: ClassVar[dict[Path, Text]] = {}

    class ContentStatic(Static): ...

    def compose(self) -> ComposeResult:
        yield ContentView.ContentStatic(markup=False)

    def on_mount(self) -> None:
        self.content_static = self.query_exactly_one(ContentView.ContentStatic)

    @work
    async def create_contents(self, path: Path) -> None:
        flat_label = self.app.query_exactly_one(FlatSectionLabel)

        if path in self.cache:
            f_content = self.cache[path]
        else:
            f_content = Text("Looks like an empty file.")
            if path in store.cm_path_sets.missing:
                f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                    self.app, path
                )
                flat_label.update(LabelStr.chezmoi_cat_output)
            elif path in store.cm_paths.any_files:
                flat_label.update(LabelStr.read_file_output)
                f_content = tchezmoi.get_highlighted_file_contents(path)
            else:
                flat_label.update(LabelStr.select_path_contents)
            self.cache[path] = f_content

        self.content_static.update(f_content)

    def on_path_changed(self, path: Path) -> None:
        self.create_contents(path)


class DiffView(BaseView):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

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

    def compose(self) -> ComposeResult:
        yield ScrollableContainer()

    def on_mount(self) -> None:
        self.diff_container = self.query_exactly_one(ScrollableContainer)

    async def get_diff_widgets(self, diff_cmd: ReadCmd, path: Path) -> list[Static]:
        if path not in store.cm_path_sets.status_paths:
            return []
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
        flat_label = self.app.query_exactly_one(FlatSectionLabel)
        cached: list[Static] = []

        if path in self.cache:
            cached = self.cache[path]
            if not cached and flat_label.display is False:
                self.diff_container.remove_children()
                flat_label.display = True
                return

        self.diff_container.loading = True
        flat_label.display = False
        self.diff_container.remove_children()

        if cached:
            self.diff_container.mount_all(self.cache[path])
        else:
            diff_statics = await self.get_diff_widgets(ReadCmd.diff, path)
            self.cache[path] = diff_statics
            self.diff_container.mount_all(self.cache[path])

        self.diff_container.loading = False

    def on_path_changed(self, path: Path) -> None:
        self._update_diff_view(path)


class DiffReverseView(BaseView):
    cache: ClassVar[dict[Path, Text]] = {}

    class DiffReverseStatic(Static): ...

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield DiffReverseView.DiffReverseStatic()

    def on_mount(self) -> None:
        self.diff_cmd = ReadCmd.diff
        self.diff_static = self.query_exactly_one(DiffReverseView.DiffReverseStatic)

    def on_path_changed(self, path: Path) -> None:
        pass


class GitLogView(BaseView):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cache: ClassVar[dict[Path, list[Static]]] = {}

    def compose(self) -> ComposeResult:
        yield DataTable[str](show_cursor=False)

    def on_mount(self) -> None:
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")
        self.data_cache: dict[Path, list[list[str]]] = {}

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
        if path in self.data_cache:
            pretty_cells = self.data_cache[path]
        else:
            path_arg = None if path == store.cfg.dest_dir else path
            cmd_result = await tchezmoi.run_chezmoi_cmd(
                self.app, ReadCmd.git_log, path_arg
            )
            pretty_cells = await self._get_styled_cells(cmd_result.out_list)
            self.data_cache[path] = pretty_cells

        for row in pretty_cells:
            self.data_table.add_row(*row)
        self.data_table.display = True

    def _can_show_diff(self, path: Path) -> bool:
        return (
            path != store.cfg.dest_dir and path not in store.cm_path_sets.managed_paths
        )

    def on_path_changed(self, path: Path) -> None:
        flat_label = self.app.query_exactly_one(FlatSectionLabel)

        if self._can_show_diff(path) and flat_label.display:
            return
        if self._can_show_diff(path) and not flat_label.display:
            self.data_table.display = False
            flat_label.display = True
            flat_label.update(LabelStr.select_path_git_log)
            return
        elif path == store.cfg.dest_dir or path in store.cm_paths.managed_dirs:
            flat_label.display = False
            self._update_datatable(path)
            self.data_table.display = True


class OperateViews(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(classes=Tcss.operations_middle)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel()
        yield SubSectionLabel()
        yield FlatSectionLabel()
        yield GitLogView()
        yield ContentView()
        yield DiffView()
        yield DiffReverseView()

    def on_mount(self) -> None:
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.content_view = self.query_exactly_one(ContentView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)

    def _set_main_section_label(self, path: Path) -> None:
        main_label = LabelStr.not_set
        if path == store.cfg.dest_dir:
            main_label = LabelStr.dest_dir
        if path in store.cm_paths.managed_dirs:
            main_label = LabelStr.managed_dir
        if path in store.cm_paths.managed_files:
            main_label = LabelStr.managed_file
        if path in store.cm_paths.status_files:
            main_label = LabelStr.status_file
        if path in store.cm_paths.un_man_dirs:
            main_label = LabelStr.unmanaged_dir
        if path in store.cm_paths.un_man_files:
            main_label = LabelStr.unmanaged_file
        self.main_section_label.update(main_label)

    def watch_path(self, path: Path | None) -> None:
        if path is None:
            return

        self._set_main_section_label(path)
        self.sub_section_label.update(str(path))

        # Propagate the path down to child views
        self.git_log_view.path = path
        self.content_view.path = path
        self.diff_view.path = path
        self.diff_reverse_view.path = path
