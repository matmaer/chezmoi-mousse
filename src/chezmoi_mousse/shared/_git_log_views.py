from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import AppType, CanvasName, DataTableName, ReadCmd, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds, CommandResult

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable

__all__ = ["GitLogView"]


class GitLogView(Vertical, AppType):

    destDir: "Path | None" = None
    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        super().__init__(
            id=ids.view.git_log, classes=Tcss.border_title_top.name
        )
        self.ids = ids
        self.git_log_table_id = ids.datatable_id(
            data_table_name=DataTableName.git_path_log_table
        )
        self.git_log_table_qid = ids.datatable_id(
            "#", data_table_name=DataTableName.git_path_log_table
        )

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.git_log_table_id, show_cursor=False)

    def on_mount(self) -> None:
        if self.ids.canvas_name != CanvasName.logs_tab:
            self.border_title = f" {self.destDir} "
        else:
            self.remove_class(Tcss.border_title_top.name)

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        datatable = self.query_one(self.git_log_table_qid, DataTableText)
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        datatable.add_row(*row)

    def populate_data_table(self, command_result: "CommandResult") -> None:
        cmd_output = command_result.std_out
        datatable = self.query_one(self.git_log_table_qid, DataTableText)
        datatable.clear(columns=True)
        datatable.add_columns("COMMIT", "MESSAGE")
        styles = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        for line in cmd_output.splitlines():
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, styles["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, styles["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, styles["error"])
            else:
                datatable.add_row(*(Text(cell) for cell in columns))

    def watch_path(self) -> None:
        if self.path is None:
            return

        if self.ids.canvas_name != CanvasName.logs_tab:
            self.border_title = f" {self.path} "

        source_path_str: str = self.app.chezmoi.read(
            ReadCmd.source_path, self.path
        ).std_out
        git_log_result: "CommandResult" = self.app.chezmoi.read(
            ReadCmd.git_log, Path(source_path_str)
        )
        self.populate_data_table(git_log_result)
