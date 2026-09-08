from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse.functions import Commands
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

    from .messages import CurrentNodeMsg

__all__ = ["GitLogView"]


class GitLogView(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    node_msg: reactive[CurrentNodeMsg | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.container.git_log)

    def compose(self) -> ComposeResult:
        yield FlatSectionLabel()
        yield DataTable[str](show_cursor=False)
        yield InfoVertical()

    def on_mount(self) -> None:
        self.git_log_results: dict[Path, tuple[str, str]]
        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)
        self.data_table: DataTable[str] = self.query_exactly_one(DataTable)
        self.data_table.add_columns("COMMIT", "MESSAGE")
        self.info_container = self.query_exactly_one(InfoVertical)
        self.info_container.display = False

    @work
    async def _update_datatable(self, node_msg: CurrentNodeMsg) -> None:
        result = await Commands.run_chezmoi_git_log(node_msg.path)
        git_log_lines = result.std_out.splitlines()

        self.data_table.clear()

        def add_row_with_style(columns: list[str], log_color: ColorVar) -> None:
            color = self.app.theme_variables[log_color]
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

    def watch_node_msg(self, node_msg: CurrentNodeMsg | None) -> None:
        if node_msg is None:
            return
        self.flat_section_label.update(str(node_msg.path))
        self._update_datatable(node_msg)
