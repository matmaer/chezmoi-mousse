from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import AppType, CanvasName, ReadCmd, Tcss, ViewName

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

    from .canvas_ids import CanvasIds

__all__ = ["GitLogView"]


class GitLogView(DataTable[Text], AppType):

    destDir: "Path | None" = None
    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.git_log_view), show_cursor=False
        )
        self.click_file_path = Text(
            "Click a file path in the tree to see the contents.", style="dim"
        )

    def on_mount(self) -> None:
        if self.ids.canvas_name in (
            CanvasName.add_tab,
            CanvasName.apply_tab,
            CanvasName.re_add_tab,
        ):
            self.add_class(Tcss.border_title_top.name)
            self.border_title = f" {self.destDir} "
            self.add_columns(
                Text('This is the destination directory "chezmoi destDir"')
            )
            self.add_row(self.click_file_path)
            return
        if self.ids.canvas_name == CanvasName.logs_tab:
            git_log_result: "CommandResult" = self.app.chezmoi.read(
                ReadCmd.git_log
            )
            self.populate_data_table(git_log_result.std_out)

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        self.add_row(*row)

    def populate_data_table(self, cmd_output: str) -> None:
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
        styles = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        for line in cmd_output.splitlines():
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, styles["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, styles["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, styles["error"])
            else:
                self.add_row(*(Text(cell) for cell in columns))

    def watch_path(self) -> None:
        if self.path is None:
            return
        self.border_title = f" {self.path} "
        source_path_str: str = self.app.chezmoi.read(
            ReadCmd.source_path, self.path
        ).std_out
        git_log_result: "CommandResult" = self.app.chezmoi.read(
            ReadCmd.git_log, Path(source_path_str)
        )
        self.border_title = f" {self.path} "
        self.populate_data_table(git_log_result.std_out)
