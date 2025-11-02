from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import RichLog

from chezmoi_mousse import AppType, LogUtils, ReadCmd, Tcss, ViewName

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CommandResult

    from .canvas_ids import CanvasIds

__all__ = ["ContentsView"]


class ContentsView(RichLog, AppType):

    destDir: "Path | None" = None
    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
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
        self.border_title = f" {self.destDir} "

    def write_managed_directory(self) -> None:
        self.write(f"Managed directory: {self.path}")
        self.write(self.click_file_path)

    def watch_path(self) -> None:
        if self.path is None or self.path == self.destDir:
            return
        self.clear()
        truncated_message = ""
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated_message = (
                    "\n\n--- File content truncated to 150 KiB ---\n"
                )
                self.write(
                    f"File {self.path} is larger than 150 KiB, truncating output."
                )
        except PermissionError as e:
            self.write(e.strerror)
            self.write(f"Permission denied to read {self.path}")
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if file_content.strip() == "":
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
            if self.path in self.app.chezmoi.dirs:
                self.write_managed_directory()
                return
            elif self.path in self.app.chezmoi.files:
                pretty_cmd = LogUtils.pretty_cmd_str(
                    ReadCmd.cat.value + [str(self.path)]
                )
                cat_output: "CommandResult" = self.app.chezmoi.read(
                    ReadCmd.cat, self.path
                )
                self.write(
                    f"File does not exist on disk, output from '{pretty_cmd}':\n"
                )
                if cat_output.std_out == "":
                    self.write(
                        Text("File contains only whitespace", style="dim")
                    )
                else:
                    self.write(cat_output.std_out)
                return

        except IsADirectoryError:
            if self.path in self.app.chezmoi.dirs:
                self.write_managed_directory()
            else:
                self.write(f"Unmanaged directory: {self.path}")
                self.write(self.click_file_path)

        except OSError as error:
            self.write(Text(f"Error reading {self.path}: {error}"))
            self.write(self.click_file_path)
