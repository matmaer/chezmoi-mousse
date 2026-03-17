from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import CMD, AppType, ReadCmd

from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["GitLogView"]


class GitLogView(Container, AppType):

    show_path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.git_log)
        self.container_cache: dict[Path, ScrollableContainer] = {}
        self.current_path: Path | None = None

    def _create_datatable_container(
        self, git_log_lines: list[str]
    ) -> ScrollableContainer:
        data_table = DataTable[str](cursor_type="row")

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
        if container is not None:
            if self.current_path is not None:
                self.container_cache[self.current_path].display = False
            container.display = True
            self.current_path = show_path
        if container is None:
            if show_path == CMD.cache.dest_dir:
                container = self._create_datatable_container(
                    CMD.cmd_results.global_git_log_lines
                )
            else:
                cmd_result = CMD.run_cmd.read(ReadCmd.git_log, path_arg=show_path)
                self.post_message(LogCmdResultMsg(cmd_result))
                container = self._create_datatable_container(
                    cmd_result.std_out.splitlines()
                )
            self.mount(container)
            self.current_path = show_path

    def purge_mounted_containers(self) -> None:
        for cached_path in list(self.container_cache.keys()):
            container = self.container_cache.pop(cached_path, None)
            if container is not None:
                container.remove()
