from itertools import groupby
from typing import TYPE_CHECKING

from textual import work
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Static

from chezmoi_mousse import (
    CMD,
    AppIds,
    AppType,
    CommandResult,
    LogString,
    ReadCmd,
    TabName,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ContentsView", "DiffView", "GitLog", "GitLogTable"]

type GitLogTableDict = dict[Path, DataTable[str]]
type DiffWidgetDict = dict[Path, list[Static]]


class ContentsView(Vertical, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        self.border_title = f" {self.app.cmd_results.dest_dir} "

    def watch_path(self) -> None:
        if self.path is None:
            return
        if self.app.paths is None:
            raise ValueError("self.app.paths is None in ContentsView watch_path")
        self.remove_children()
        self.mount(self.app.paths.contents_dict[self.path])


class DiffWidgets:
    DIFF_TCSS = {
        "diff --git a/": Tcss.command,
        " ": Tcss.context,
        "@@": Tcss.context,
        "index": Tcss.context,
        "-": Tcss.removed,
        "deleted": Tcss.removed,
        "old": Tcss.removed,
        "+": Tcss.added,
        "new": Tcss.added,
        "changed": Tcss.changed,
        "unhandled": Tcss.unhandled,
    }

    def __init__(self, diff_result: CommandResult) -> None:
        self.widgets: list[Static] = []
        if not diff_result.std_out:
            self.widgets = [Static(LogString.no_stdout)]
            return

        lines = diff_result.std_out.splitlines()

        def get_prefix(line: str) -> str:
            for p in self.DIFF_TCSS:
                if line.startswith(p):
                    return p
            return "unhandled"

        for prefix, group_lines in groupby(lines, key=get_prefix):
            group_list = list(group_lines)
            if prefix in ("+", "-"):
                text = "\n".join(group_list)
                self.widgets.append(Static(text, classes=self.DIFF_TCSS[prefix].value))
            else:
                for line in group_list:
                    self.widgets.append(
                        Static(line, classes=self.DIFF_TCSS[prefix].value)
                    )


class DiffView(ScrollableContainer, AppType):

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.diff, classes=Tcss.border_title_top)
        self.diff_widgets: DiffWidgetDict = {}
        self.canvas_name = ids.canvas_name

    def on_mount(self) -> None:
        self.border_title = f" {self.app.cmd_results.dest_dir} "

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return
        if (
            self.canvas_name == TabName.apply
            and self.show_path not in self.diff_widgets
        ):
            self.diff_widgets[self.show_path] = DiffWidgets(
                CMD.read(ReadCmd.diff, path_arg=self.show_path)
            ).widgets
        elif (
            self.canvas_name == TabName.re_add
            and self.show_path not in self.diff_widgets
        ):
            self.diff_widgets[self.show_path] = DiffWidgets(
                CMD.read(ReadCmd.diff_reverse, path_arg=self.show_path)
            ).widgets

        self.remove_children()
        self.mount_all(self.diff_widgets[self.show_path])


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
