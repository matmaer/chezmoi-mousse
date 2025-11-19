from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import AppType, ReadCmd, Tcss
from chezmoi_mousse._names import CanvasName

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds, CommandResult

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable

__all__ = ["GitLogPath", "GitLogGlobal"]


class GitLogbase(Vertical, AppType):

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        if self.ids.canvas_name == CanvasName.logs_tab:
            self.data_table_id = self.ids.data_table.git_global_log
            self.data_table_qid = self.ids.data_table.git_global_log_q
        else:
            self.data_table_id = self.ids.data_table.git_path_log
            self.data_table_qid = self.ids.data_table.git_path_log_q
        super().__init__(
            id=self.ids.container.git_log, classes=Tcss.border_title_top.name
        )

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        datatable = self.query_one(self.data_table_qid, DataTableText)
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        datatable.add_row(*row)

    def populate_data_table(self, command_result: "CommandResult") -> None:
        cmd_output = command_result.std_out
        datatable = self.query_one(self.data_table_qid, DataTableText)
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


class GitLogPath(GitLogbase, AppType):

    destDir: "Path | None" = None
    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.ids.data_table.git_path_log, show_cursor=False)

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        self.add_class(Tcss.border_title_top.name)

    def watch_path(self) -> None:
        if self.path is None:
            return

        source_path_str: str = self.app.chezmoi.read(
            ReadCmd.source_path, self.path
        ).std_out
        git_log_result: "CommandResult" = self.app.chezmoi.read(
            ReadCmd.git_log, Path(source_path_str)
        )
        self.populate_data_table(git_log_result)


class GitLogGlobal(GitLogbase, AppType):

    git_log_result: reactive["CommandResult | None"] = reactive(
        None, init=False
    )

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.data_table_id, show_cursor=False)

    def on_mount(self) -> None:
        self.remove_class(Tcss.border_title_top.name)

    def watch_git_log_result(self) -> None:
        if self.git_log_result is None:
            return

        self.populate_data_table(self.git_log_result)
