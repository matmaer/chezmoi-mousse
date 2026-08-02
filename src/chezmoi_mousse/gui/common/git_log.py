from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import getters
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import ColorVar

from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui

__all__ = ["GitLogView"]


class GitLogView(Container):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_path: reactive[Path | None] = reactive(None)

    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.container.git_log)

    def _create_datatable_container(
        self, git_log_lines: list[str]
    ) -> ScrollableContainer:
        data_table = DataTable[str](cursor_type="row")

        def add_row_with_style(columns: list[str], log_color: ColorVar) -> None:
            color = self.app.get_color(log_color)
            row: list[str] = [f"[{color}]{cell_text}[/]" for cell_text in columns]
            data_table.add_row(*row)

        data_table.add_columns("COMMIT", "MESSAGE")
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
        return ScrollableContainer(data_table)

    def watch_show_path(self, show_path: Path | None) -> None:
        path_arg = None if show_path == self.app.cmattr.dest_dir else show_path
        self.remove_children()
        cmd_result = Commands.run_chezmoi_git_log(path_arg)
        self.post_message(LogCmdResultMsg(cmd_result))
        container = self._create_datatable_container(cmd_result.std_out.splitlines())
        self.mount(container)
