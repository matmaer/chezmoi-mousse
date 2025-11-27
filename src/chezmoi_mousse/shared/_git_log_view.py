from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import AppType, ReadCmd, Tcss

from ._dest_dir_info import DestDirInfo

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, CommandResult

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable

__all__ = ["GitLogPath", "GitLogGlobal"]


class GitLogDataTable(DataTable[Text], AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.datatable.git_log)

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        self.add_row(*row)

    def populate_datatable(self, command_result: "CommandResult") -> None:
        cmd_output = command_result.std_out
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
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
                self.add_row(*(Text(cell) for cell in columns))


class GitLogPath(Vertical, AppType):

    destDir: "Path | None" = None
    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.git_log_path, classes=Tcss.border_title_top
        )

    def compose(self) -> ComposeResult:
        yield GitLogDataTable(ids=self.ids)
        yield DestDirInfo(ids=self.ids, git_log=True)

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "

    def watch_path(self) -> None:
        if self.path is None:
            return
        else:
            dest_dir_info = self.query_one(
                self.ids.container.dest_dir_info_q, DestDirInfo
            )
            dest_dir_info.visible = False
        datatable = self.query_one(
            self.ids.datatable.git_log_q, GitLogDataTable
        )
        command_result: "CommandResult" = self.app.chezmoi.read(
            ReadCmd.source_path, self.path
        )
        git_log_result: "CommandResult" = self.app.chezmoi.read(
            ReadCmd.git_log, Path(command_result.std_out)
        )
        datatable.populate_datatable(git_log_result)


class GitLogGlobal(Vertical, AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.git_log_global)

    def compose(self) -> ComposeResult:
        yield GitLogDataTable(ids=self.ids)

    def update_global_git_log(self, command_result: "CommandResult") -> None:
        datatable = self.query_one(
            self.ids.datatable.git_log_q, GitLogDataTable
        )
        datatable.populate_datatable(command_result)
