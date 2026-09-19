from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    LabeledView,
    MainSectionLabel,
    SubSectionLabel,
)
from chezmoi_mousse.str_enums import ColorVar, LabelStr, ReadCmd, StatusCode

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["ContentsView", "GitLogView"]


main_title_mapping: dict[StatusCode, LabelStr] = {StatusCode.UU: LabelStr.unmanaged_dir}


class HighlightedStatic(Static): ...


class ContentsView(LabeledView):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds, classes: str) -> None:
        super().__init__(
            container_id=ids.container.contents,
            main_label=LabelStr.dest_dir,
            sub_label=LabelStr.not_set,
            flat_label=LabelStr.not_set,
            view_body=HighlightedStatic(markup=False),
            classes=classes,
        )

    def on_mount(self) -> None:
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)
        self.highlighted_static = self.query_exactly_one(HighlightedStatic)

    def _set_dir_contents(self, path: Path) -> None:
        # main label
        if path == store.cfg.dest_dir:
            self.main_section_label.update(LabelStr.dest_dir)
        elif path in store.cm_paths.managed_dirs:
            self.main_section_label.update(LabelStr.managed_dir)
        else:
            self.main_section_label.update(LabelStr.unmanaged_dir)

    @work
    async def _create_unknown_path_container(self) -> None:
        self.main_section_label.update(LabelStr.unmanaged_path)
        self.sub_section_label.update(str(self.path))

    @work
    async def _create_file_container(self, path: Path) -> None:
        self.main_section_label.update(LabelStr.not_set)
        if path in store.cm_paths.managed_files:
            self.main_section_label.update(LabelStr.managed_file)
        else:
            self.main_section_label.update(LabelStr.unmanaged_file)
        if path in store.cm_path_sets.missing:
            f_content = await tchezmoi.get_highlighted_chezmoi_cat_output(
                self.app, path
            )
            self.highlighted_static.update(f_content)
            self.flat_section_label.update(LabelStr.chezmoi_cat_output)
        else:
            f_content = tchezmoi.get_highlighted_file_contents(path)
            self.highlighted_static.update(f_content)
            self.flat_section_label.update(LabelStr.read_file_output)

    def watch_path(self, path: Path) -> None:
        if (
            path == store.cfg.dest_dir
            or path in store.cm_paths.any_dirs
            or path.is_dir()
        ):
            self._set_dir_contents(path)
        elif path in store.cm_paths.any_files or path.is_file():
            self._create_file_container(path)
        else:
            self._create_unknown_path_container()


class GitLogView(LabeledView):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds, classes: str) -> None:
        super().__init__(
            container_id=ids.container.git_log,
            main_label=LabelStr.dest_dir,
            sub_label=LabelStr.not_set,
            flat_label=LabelStr.unmanaged_path,
            view_body=DataTable[str](show_cursor=False),
            classes=classes,
        )

    def on_mount(self) -> None:
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")
        self.data_cache: dict[Path, list[list[str]]] = {}
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)

    async def _create_stylized_lines(self, log_lines: list[str]) -> list[list[str]]:
        pretty_rows: list[list[str]] = []

        def stylize(columns: list[str], log_color: ColorVar) -> None:
            color = self.app.theme_variables[log_color]
            row: list[str] = [f"[{color}]{cell_text}[/]" for cell_text in columns]
            pretty_rows.append(row)

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

        return pretty_rows

    @work
    async def _update_datatable(self, path: Path) -> None:
        self.data_table.clear()
        if path != store.cfg.dest_dir and path not in store.cm_path_sets.managed_paths:
            self.data_table.display = False
            self.main_section_label.update(LabelStr.git_log)
            self.sub_section_label.update(str(path))
            self.sub_section_label.display = True
            self.flat_section_label.display = True
            return
        self.main_section_label.update(tchezmoi.pretty_cmd(ReadCmd.git_log, path))
        self.sub_section_label.display = False
        self.flat_section_label.display = False
        if path in self.data_cache:
            pretty_rows = self.data_cache[path]
        else:
            path_arg = None if path == store.cfg.dest_dir else path
            cmd_result = await tchezmoi.run_chezmoi_command(
                self.app, ReadCmd.git_log, path_arg
            )
            pretty_rows = await self._create_stylized_lines(cmd_result.out_list)
            self.data_cache[path] = pretty_rows
        for row in pretty_rows:
            self.data_table.add_row(*row)
        self.data_table.display = True

    async def watch_path(self, path: Path) -> None:
        self.data_table.loading = True
        self._update_datatable(path)
        self.data_table.loading = False
