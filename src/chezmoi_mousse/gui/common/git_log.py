from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters
from textual.app import ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import store
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import ColorVar

from .components import FlatSectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["GitLogView"]


class GitLogView(Container):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_path: reactive[Path | None] = reactive(None)

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.container.git_log)

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel()
        yield DataTable[str](fixed_rows=1, show_cursor=False)

    def on_mount(self) -> None:
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table = self.query_exactly_one(DataTable[str])
        self.data_table.add_columns("COMMIT", "MESSAGE")

    def _update_datatable(self, git_log_lines: list[str]) -> None:
        self.data_table.clear()

        def add_row_with_style(columns: list[str], log_color: ColorVar) -> None:
            color = self.app.get_color(log_color)
            row: list[str] = [f"[{color}]{cell_text}[/]" for cell_text in columns]
            self.data_table.add_row(*row)

        for line in git_log_lines:
            no_commit_message = "no commit message"
            rel_date, committer, subject = line.rstrip("\x00").split("\x1f", 2)
            column_one = f"{rel_date} by {committer}"
            column_two = f"{subject}" if subject.strip() else no_commit_message
            columns: list[str] = [column_one, column_two]
            if column_two.split(maxsplit=1)[0] == "Add":
                add_row_with_style(columns, ColorVar.text_success)
            elif column_two.split(maxsplit=1)[0] == "Update":
                add_row_with_style(columns, ColorVar.text_warning)
            elif column_two.split(maxsplit=1)[0] == "Remove":
                add_row_with_style(columns, ColorVar.text_error)
            elif column_two == no_commit_message:
                add_row_with_style(columns, ColorVar.text_secondary)
            else:
                add_row_with_style(columns, ColorVar.text)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        if (
            show_path != self.app.cmattr.dest_dir
            and show_path not in self.app.cmattr.paths.managed_paths_set
        ):
            return
        if show_path == self.app.cmattr.dest_dir:
            self.flat_section_label.update(store.git_log_result.pretty_cmd)
            self._update_datatable(store.git_log_result.std_out.splitlines())
        else:
            cmd_results = Commands.run_chezmoi_git_log(show_path)
            self.flat_section_label.update(cmd_results.pretty_cmd)
            self._update_datatable(cmd_results.std_out.splitlines())
