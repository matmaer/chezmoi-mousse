from pathlib import Path

from textual import work
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import DataTable

from chezmoi_mousse import CMD, AppIds, AppType, CommandResult, ReadCmd, Tcss

__all__ = ["GitLog", "GitLogTable"]


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


class GitLog(Container, AppType):

    changed_paths: reactive["list[Path] | None"] = reactive(None, init=False)
    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.git_log, classes=Tcss.border_title_top)
        self.cache: dict[Path, ScrollableContainer] = {}
        self.current_container: ScrollableContainer | None = None

    def on_mount(self) -> None:
        self.border_title = " Global Chezmoi Git Log "

    def _cache_container(
        self, path: Path, table: DataTable[str]
    ) -> ScrollableContainer:
        """Helper to mount and cache a ScrollableContainer with DataTable."""
        container = ScrollableContainer()
        self.mount(container)
        container.mount(table)
        self.cache[path] = container
        return container

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return

        if self.show_path not in self.cache:
            table = GitLogTable(CMD.read(ReadCmd.git_log, path_arg=self.show_path))
            self._cache_container(self.show_path, table)

        if self.show_path != self.app.dest_dir:
            self.border_title = f" {self.show_path.name} "
        # Hide current container, show the selected one
        if self.current_container is not None:
            self.current_container.display = False
        self.cache[self.show_path].display = True
        self.current_container = self.cache[self.show_path]

    @work
    async def watch_changed_paths(self) -> None:
        if self.changed_paths is None:
            return

        # Remove cached paths no longer in changed_paths
        paths_to_remove = [p for p in self.cache if p not in self.changed_paths]
        for path in paths_to_remove:
            self.cache.pop(path, None)

        # Add new paths from changed_paths that aren't cached yet
        for path in self.changed_paths:
            if path not in self.cache:
                table = GitLogTable(CMD.read(ReadCmd.git_log, path_arg=path))
                self._cache_container(path, table)
