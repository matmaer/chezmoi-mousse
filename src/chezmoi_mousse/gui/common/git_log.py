from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    InfoVertical,
)
from chezmoi_mousse.str_enums import ColorVar

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult


__all__ = ["GitLogView"]


class GitLogView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.container.git_log)

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel()
        yield DataTable(show_cursor=False)
        yield InfoVertical()

    def on_mount(self) -> None:
        self.git_log_results: dict[Path, tuple[str, str]]
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")
        self.info_container = self.query_exactly_one(InfoVertical)
        self.info_container.display = False

    @work
    async def _update_datatable(self, std_out: str) -> None:
        git_log_lines = std_out.splitlines()

        pretty_rows: list[list[str]] = []

        def stylize(columns: list[str], log_color: ColorVar) -> None:
            color = self.app.theme_variables[log_color]
            row: list[str] = [f"[{color}]{cell_text}[/]" for cell_text in columns]
            pretty_rows.append(row)

        for line in git_log_lines:
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
                stylize(columns, ColorVar.text)

        self.data_table.clear()

        for row in pretty_rows:
            self.data_table.add_row(*row)

    def watch_cmd_result(self, cmd_result: CommandResult | None) -> None:
        if cmd_result is None:
            return
        if cmd_result.path_arg is None:
            self.flat_section_label.update(str(store.cfg.dest_dir))
        else:
            self.flat_section_label.update(str(cmd_result.path_arg))
        self._update_datatable(cmd_result.std_out)
