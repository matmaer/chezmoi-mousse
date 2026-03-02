from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import CMD, AppType, ReadCmd, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["GitLog"]


class GitLog(ScrollableContainer, AppType):

    show_path: reactive[Path] = reactive(CMD.dest_dir)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.git_log, classes=Tcss.border_title_top)
        self.data_table_cache: dict[Path, DataTable[str]] = {}
        self.current_data_table: DataTable[str] = DataTable[str]()

    def _set_border_title(self) -> None:
        if self.show_path == CMD.dest_dir:
            self.border_title = " Global Chezmoi Git Log "
        else:
            self.border_title = f" {self.show_path.name} "

    def _mount_and_cache_data_table(self, path: Path, table: DataTable[str]):
        self.current_data_table.display = False
        self.mount(table)
        self.data_table_cache[path] = table
        self.current_data_table = self.data_table_cache[self.show_path]

    def _create_datatable(self, git_log_lines: list[str]) -> DataTable[str]:
        data_table = DataTable[str]()

        def add_row_with_style(columns: list[str], style: str) -> None:
            row: list[str] = [
                f"[{style}]{cell_text}[/{style}]" for cell_text in columns
            ]
            data_table.add_row(*row)

        row_color = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        data_table.add_columns("COMMIT", "MESSAGE")
        for line in git_log_lines:
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                add_row_with_style(columns, row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                add_row_with_style(columns, row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                add_row_with_style(columns, row_color["error"])
            else:
                data_table.add_row(*columns)
        return data_table

    def watch_show_path(self, show_path: Path) -> None:
        if show_path in self.data_table_cache:
            self.current_data_table.display = False
            self.data_table_cache[show_path].display = True
            self.current_data_table = self.data_table_cache[self.show_path]
            self._set_border_title()
            return
        if show_path == CMD.dest_dir:
            table = self._create_datatable(CMD.global_git_log_lines)
        else:
            cmd_result = CMD.run_cmd.read(ReadCmd.git_log, path_arg=self.show_path)
            table = self._create_datatable(cmd_result.std_out.splitlines())
        self._set_border_title()
        self._mount_and_cache_data_table(self.show_path, table)
