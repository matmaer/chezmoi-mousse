from pathlib import Path

from textual import work
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import CMD, AppIds, AppType, CommandResult, ReadCmd, Tcss

__all__ = ["GitLog", "GitLogTable"]

type GitLogTableDict = dict[Path, DataTable[str]]


class GitLogTable(DataTable[str], AppType):

    def __init__(self, git_log_result: CommandResult) -> None:
        super().__init__()
        self.git_log_result = git_log_result

    def on_mount(self) -> None:
        self._populate_datatable()

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: list[str] = [f"[{style}]{cell_text}[/{style}]" for cell_text in columns]
        self.add_row(*row)

    def _populate_datatable(self) -> None:
        row_color = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        self.add_columns("COMMIT", "MESSAGE")
        lines = self.git_log_result.std_out.splitlines()
        if len(lines) == 0:
            self.add_row("No commits;No git log available for this path.")
            return
        for line in lines:
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, row_color["error"])
            else:
                self.add_row(*columns)


class GitLog(ScrollableContainer, AppType):

    changed_managed_paths: reactive["list[Path] | None"] = reactive(None, init=False)
    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.git_log, classes=Tcss.border_title_top)
        self.git_log_tables: GitLogTableDict = {}

    def on_mount(self) -> None:
        self.border_title = f" {self.app.cmd_results.dest_dir} "

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return
        self.remove_children()
        if self.show_path not in self.git_log_tables:
            self.git_log_tables[self.show_path] = GitLogTable(
                CMD.read(ReadCmd.git_log, path_arg=self.show_path)
            )
        self.mount(self.git_log_tables[self.show_path])

    @work
    async def watch_changed_managed_paths(self) -> None:
        if self.changed_managed_paths is None:
            return
        for path in self.changed_managed_paths:
            # remove paths no longer in managed_paths
            if path not in self.git_log_tables:
                self.git_log_tables.pop(path, None)
            # add paths in managed_paths that are not in git_log_tables
            self.git_log_tables[path] = GitLogTable(
                CMD.read(ReadCmd.git_log, path_arg=path)
            )
