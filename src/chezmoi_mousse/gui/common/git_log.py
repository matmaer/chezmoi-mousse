from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import CMD, ReadCmd

from .mixins import ContainerCache

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["GitLogView"]


class GitLogView(ContainerCache):

    show_path: reactive[Path | None] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.git_log)
        self.container_cache: dict[Path, ScrollableContainer] = {}
        self.current_container_path: Path | None = None

    def on_mount(self) -> None:
        self.show_path = CMD.cache.dest_dir

    def _create_datatable_container(
        self, git_log_lines: list[str]
    ) -> ScrollableContainer:
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
        return ScrollableContainer(data_table)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        container = self.container_cache.get(show_path, None)
        new_container: ScrollableContainer | None = None
        if container is None:
            # Create new table
            if show_path == CMD.cache.dest_dir:
                new_container = self._create_datatable_container(
                    CMD.cache.global_git_log_lines
                )
            else:
                cmd_result = CMD.run_cmd.read(ReadCmd.git_log, path_arg=show_path)
                self.app.log_cmd_result(cmd_result)
                new_container = self._create_datatable_container(
                    cmd_result.std_out.splitlines()
                )
        self.update_container_display(show_path, new_container)
