from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import RichLog

from chezmoi_mousse import (
    AppType,
    Canvas,
    Chars,
    LogUtils,
    ReadCmd,
    Tcss,
    ViewName,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppType, CanvasIds, CommandResults

__all__ = ["DiffView"]


class DiffView(RichLog, AppType):

    destDir: "Path | None" = None
    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds", reverse: bool) -> None:
        self.ids = ids
        self.reverse = reverse
        self.diff_read_cmd: ReadCmd = (
            ReadCmd.diff_reverse if self.reverse else ReadCmd.diff
        )
        self.pretty_diff_cmd = LogUtils.pretty_cmd_str(
            self.diff_read_cmd.value
        )
        super().__init__(
            id=self.ids.view_id(view=ViewName.diff_view),
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            classes=Tcss.border_title_top.name,
        )
        self.click_colored_file = Text(
            f"Click a path with status to see the output from {self.pretty_diff_cmd}.",
            style="dim",
        )

    def on_mount(self) -> None:
        self.write('This is the destination directory "chezmoi destDir"\n')
        self.write(self.click_colored_file)
        self.border_title = f" {self.destDir} "

    def _write_unchanged_path_info(self) -> None:
        if self.path in self.app.chezmoi.managed_paths.dirs:
            self.write(f"Managed directory {self.path}\n")
        self.write(
            f'No diff available for "{self.path}", the path has no status.\n'
        )
        if self.ids.canvas_name != Canvas.operate_launch:
            self.write(self.click_colored_file)

    def watch_path(self) -> None:
        if self.path is None or self.path == self.destDir:
            return
        self.clear()
        # write lines for an unchanged file or directory except when we are in
        # either the ApplyTab or ReAddTabS

        if self.ids.canvas_name == Canvas.apply:
            if (
                self.path
                not in self.app.chezmoi.managed_paths.apply_status_files
                and self.path
                not in self.app.chezmoi.managed_paths.apply_status_dirs
            ):
                self._write_unchanged_path_info()
                return
        else:
            if (
                self.path
                not in self.app.chezmoi.managed_paths.re_add_status_files
                and self.path
                not in self.app.chezmoi.managed_paths.re_add_status_dirs
            ):
                self._write_unchanged_path_info()
                return

        # create the diff view for a changed file
        diff_output: "CommandResults" = self.app.chezmoi.read(
            self.diff_read_cmd, self.path
        )

        self.write(f'Output from "{self.pretty_diff_cmd} {self.path}"')

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
            self.write("\nPermissions/mode will be changed:")
        for line in mode_diff_lines:
            self.write(f" {Chars.bullet} {line}")

        if len(path_diff_lines) > 0:
            self.write("\nPaths:")
        for line in path_diff_lines:
            if line.startswith("---"):
                self.write(Text(line, self.app.theme_variables["text-error"]))
            elif line.startswith("+++"):
                self.write(
                    Text(line, self.app.theme_variables["text-success"])
                )

        if len(other_diff_lines) > 0:
            self.write("\nDiff lines:")
        for line in other_diff_lines:
            if line.startswith("-"):
                self.write(Text(line, self.app.theme_variables["text-error"]))
            elif line.startswith("+"):
                self.write(
                    Text(line, self.app.theme_variables["text-success"])
                )
