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

    from chezmoi_mousse import ActiveCanvas, AppType, CanvasIds

__all__ = ["ContentsView", "DiffView"]


class ContentsView(RichLog, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        self.destDir: "Path | None" = None
        super().__init__(
            id=self.ids.view_id(view=ViewName.contents_view),
            auto_scroll=False,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            highlight=True,
            classes=Tcss.border_title_top.name,
        )
        self.click_file_path = Text(
            "\nClick a file path in the tree to see the contents.", style="dim"
        )

    def on_mount(self) -> None:
        self.write('This is the destination directory "chezmoi destDir"')
        self.write(self.click_file_path)

    def watch_path(self) -> None:
        assert self.path is not None
        self.border_title = f" {self.path} "
        if self.path == self.destDir:
            return
        self.clear()
        truncated_message = ""
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated_message = (
                    "\n\n--- File content truncated to 150 KiB ---\n"
                )
                self.app.app_log.warning(
                    f"File {self.path} is larger than 150 KiB, truncating output."
                )
        except PermissionError as e:
            self.write(e.strerror)
            self.app.app_log.error(f"Permission denied to read {self.path}")
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if not file_content.strip():
                    message = "File is empty or contains only whitespace"
                    self.write(message)
                else:
                    self.write(file_content + truncated_message)

        except UnicodeDecodeError:
            self.write(f"{self.path} cannot be decoded as UTF-8.")
            return

        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.path in self.app.chezmoi.managed_dirs:
                self.write(f"Managed directory: {self.path}")
                self.write(self.click_file_path)
                return
            if self.path in self.app.chezmoi.managed_files:
                cat_output = self.app.chezmoi.read(ReadCmd.cat, self.path)
                if cat_output == "":
                    self.write(
                        Text("File contains only whitespace", style="dim")
                    )
                else:
                    self.write(cat_output.splitlines())
                return

        except IsADirectoryError:
            if self.path in self.app.chezmoi.managed_dirs:
                self.write(f"Managed directory: {self.path}")
                self.write(self.click_file_path)
            else:
                self.write(f"Unmanaged directory: {self.path}")
                self.write(self.click_file_path)

        except OSError as error:
            self.write(Text(f"Error reading {self.path}: {error}"))
            if self.app.chezmoi.app_log is not None:
                self.app.chezmoi.app_log.error(
                    f"Error reading {self.path}: {error}"
                )


class DiffView(RichLog, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds", reverse: bool) -> None:
        self.ids = ids
        self.reverse = reverse
        self.destDir: "Path | None" = None
        self.active_canvas: "ActiveCanvas | None" = None
        self.diff_read_cmd: ReadCmd = (
            ReadCmd.diff_reverse if self.reverse else ReadCmd.diff
        )
        self.pretty_diff_cmd = LogUtils.pretty_cmd_str(
            self.diff_read_cmd.value
        )
        self.active_canvas = Canvas.re_add if self.reverse else Canvas.apply
        super().__init__(
            id=self.ids.view_id(view=ViewName.diff_view),
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            classes=Tcss.border_title_top.name,
        )
        self.click_colored_file = Text(
            f"Click a colored file in the tree to see the output from {self.pretty_diff_cmd}.",
            style="dim",
        )

    def on_mount(self) -> None:
        self.write('This is the destination directory "chezmoi destDir"\n')
        self.write(self.click_colored_file)

    def _write_dir_info(self) -> None:
        self.write(f"Managed directory {self.path}\n")
        self.write(self.click_colored_file)

    def _write_unchanged_file_info(self) -> None:
        self.write(
            f'No diff available for "{self.path}", the file is unchanged.'
        )
        self.write(self.click_colored_file)

    def watch_path(self) -> None:
        self.border_title = f" {self.path} "
        if self.path == self.destDir:
            return
        self.clear()
        # write lines for an unchanged file or directory except when we are in
        # either the ApplyTab or ReAddTab
        if (
            self.active_canvas is not None
            and self.path in self.app.chezmoi.managed_dirs
        ):
            self._write_dir_info()
            return

        # create the diff view for a changed file
        diff_output: list[str] = []
        diff_output = self.app.chezmoi.read(
            self.diff_read_cmd, self.path
        ).splitlines()

        diff_lines: list[str] = [
            line
            for line in diff_output
            if line.strip() != ""
            and (
                line[0] in "+- "
                or line.startswith("old mode")
                or line.startswith("new mode")
            )
            and not line.startswith(("+++", "---"))
        ]
        if not diff_lines:
            self._write_unchanged_file_info()
            return

        for line in diff_lines.copy():
            line = line.rstrip("\n")  # each write call contains a newline
            if line.startswith("old mode") or line.startswith("new mode"):
                self.write("Permissions/mode will be changed:")
                self.write(f" {Chars.bullet} {line}")
                # remove the line from diff_lines
                diff_lines.remove(line)

        self.write(f'Output from "{self.pretty_diff_cmd} {self.path}":\n')
        for line in diff_lines:
            if line.startswith("-"):
                self.write(Text(line, self.app.theme_variables["text-error"]))
            elif line.startswith("+"):
                self.write(
                    Text(line, self.app.theme_variables["text-success"])
                )
