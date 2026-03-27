from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Container, ScrollableContainer
from textual.css.query import NoMatches
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
        self.mounted: dict[Path, str] = {}
        self.current_path: Path | None = None

    def hide_all_containers(self) -> None:
        for container in self.query_children(ScrollableContainer):
            container.display = False

    def _create_datatable_container(
        self, git_log_lines: list[str], path: Path
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
        return ScrollableContainer(data_table, id=self.app.path_to_id(path))

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self.hide_all_containers()
        sc_id = self.app.path_to_id(show_path)
        sc_id_q = self.app.path_to_qid(show_path)
        try:
            container = self.query_one(sc_id_q, ScrollableContainer)
            container.display = True
        except NoMatches:
            if show_path == CMD.cache.dest_dir:
                if (
                    CMD.cache.cmd_results.git_log is None
                    or not CMD.cache.cmd_results.git_log.std_out
                ):
                    git_log_lines = ["No commits;No git log entries available yet."]
                else:
                    git_log_lines = CMD.cache.cmd_results.git_log.std_out.splitlines()
                container = self._create_datatable_container(git_log_lines, show_path)
            else:
                cmd_result = CMD.run_cmd.read(ReadCmd.git_log, path_arg=show_path)
                self.post_message(LogCmdResultMsg(cmd_result))
                container = self._create_datatable_container(
                    cmd_result.std_out.splitlines(), show_path
                )
            self.mount(container)
            self.mounted[show_path] = sc_id
        self.current_path = show_path
