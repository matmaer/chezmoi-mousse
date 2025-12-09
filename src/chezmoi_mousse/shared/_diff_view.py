from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import RichLog, Static

from chezmoi_mousse import (
    AppType,
    Chars,
    DestDirStrings,
    ReadCmd,
    SectionLabels,
    TabName,
    Tcss,
)

from ._section_headers import SubSectionLabel

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, AppType, CommandResult

__all__ = ["DiffView"]


class DiffView(Vertical, AppType):

    destDir: "Path | None" = None
    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds", reverse: bool) -> None:
        self.ids = ids
        self.reverse = reverse
        self.diff_cmd: ReadCmd = (
            ReadCmd.diff_reverse if self.reverse else ReadCmd.diff
        )
        super().__init__(
            id=self.ids.container.diff_view, classes=Tcss.border_title_top
        )

    def compose(self) -> ComposeResult:
        with Vertical(id=self.ids.container.dest_dir_info):
            yield SubSectionLabel(SectionLabels.path_info)
            yield Static(DestDirStrings.diff)
        yield RichLog(
            id=self.ids.logger.diff,
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
        )

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "

    def _write_unchanged_path_info(self) -> None:
        if self.path in self.app.chezmoi.dirs:
            self.rich_log.write(f"Managed directory {self.path}\n")
        self.rich_log.write(
            f'No diff available for "{self.path}", the path has no status.\n'
        )

    def watch_path(self) -> None:
        if self.path is None:
            return
        else:
            dest_dir_info = self.query_one(
                self.ids.container.dest_dir_info_q, Vertical
            )
            dest_dir_info.display = False
        self.border_title = f" {self.path} "
        self.rich_log = self.query_one(self.ids.logger.diff_q, RichLog)
        self.rich_log.clear()

        # write lines for an unchanged file or directory
        if (
            self.ids.canvas_name == TabName.apply
            and self.path not in self.app.chezmoi.apply_status_files
            and self.path not in self.app.chezmoi.apply_status_dirs
        ):
            self._write_unchanged_path_info()
            return
        if (
            self.ids.canvas_name == TabName.re_add
            and self.path not in self.app.chezmoi.re_add_status_files
            and self.path not in self.app.chezmoi.re_add_status_dirs
        ):
            self._write_unchanged_path_info()
            return

        # create the diff view for a changed file
        diff_output: "CommandResult" = self.app.chezmoi.read(
            self.diff_cmd, path_arg=self.path
        )

        self.rich_log.write(f'Output from "{diff_output.pretty_cmd}"')

        mode_diff_lines = [
            line
            for line in diff_output.std_out.splitlines()
            if line.strip() != ""
            and (line.startswith("old mode") or line.startswith("new mode"))
            and not line.startswith(("+++", "---"))
        ]

        path_diff_lines = [
            line
            for line in diff_output.std_out.splitlines()
            if line.strip() != "" and line.startswith(("+++", "---"))
        ]

        other_diff_lines: list[str] = [
            line
            for line in diff_output.std_out.splitlines()
            if line.strip() != ""
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        ]

        if len(mode_diff_lines) > 0:
            self.rich_log.write("\nPermissions/mode will be changed:")
        for line in mode_diff_lines:
            self.rich_log.write(f" {Chars.bullet} {line}")

        if len(path_diff_lines) > 0:
            self.rich_log.write("\nPaths:")
        for line in path_diff_lines:
            if line.startswith("---"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-error"])
                )
            elif line.startswith("+++"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-success"])
                )

        if len(other_diff_lines) > 0:
            self.rich_log.write("\nDiff lines:")
        for line in other_diff_lines:
            if line.startswith("-"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-error"])
                )
            elif line.startswith("+"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-success"])
                )
