from enum import StrEnum
from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import RichLog

from chezmoi_mousse import AppType, ReadCmd, Tcss, ViewName

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CommandResult

    from .canvas_ids import CanvasIds

__all__ = ["ContentsView"]


class Strings(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    click_file_path = "Click a file path in the tree to see the contents."
    empty_or_only_whitespace = "File is empty or contains only whitespace"
    initial_msg = 'This is the destination directory "chezmoi destDir"'
    managed_dir = "Managed directory:"
    output_from_cat = "File does not exist on disk, output from"
    output_from_read = "Output from Path.read"
    permission_denied = "Permission denied to read file"
    read_error = "Error reading path:"
    too_large = "File is larger than 150 KiB, truncating output for"
    truncated = "\n--- File content truncated to 150 KiB ---\n"
    unmanaged_dir = "Unmanaged directory:"


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

    def on_mount(self) -> None:
        self.write(Strings.initial_msg)
        self.write(Strings.click_file_path)
        self.border_title = f" {self.destDir} "

    def write_managed_directory(self) -> None:
        self.write(f"{Strings.managed_dir} {self.path}")
        self.write(Strings.click_file_path)

    def watch_path(self) -> None:
        if self.path is None or self.path == self.destDir:
            return
        self.border_title = f" {self.path} "
        self.clear()
        truncated_message = ""
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated_message = Strings.truncated
                self.write(f"{Strings.too_large} {self.path}")
        except PermissionError as e:
            self.write(e.strerror)
            self.write(f"{Strings.permission_denied} {self.path}")
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if file_content.strip() == "":
                    self.write(Strings.empty_or_only_whitespace)
                else:
                    self.write(f"{Strings.output_from_read} {self.path}\n")
                    self.write(truncated_message + file_content)

        except UnicodeDecodeError:
            self.write(f"{Strings.cannot_decode} {self.path}")
            return

        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.path in self.app.chezmoi.dirs:
                self.write_managed_directory()
                return
            elif self.path in self.app.chezmoi.files:
                cat_output: "CommandResult" = self.app.chezmoi.read(
                    ReadCmd.cat, self.path
                )
                self.write(
                    f'{Strings.output_from_cat} "{cat_output.pretty_cmd}"\n'
                )
                if cat_output.std_out == "":
                    self.write(
                        Text(Strings.empty_or_only_whitespace, style="dim")
                    )
                else:
                    self.write(cat_output.std_out)
                return

        except IsADirectoryError:
            if self.path in self.app.chezmoi.dirs:
                self.write_managed_directory()
            else:
                self.write(f"{Strings.unmanaged_dir} {self.path}")
                self.write(Strings.click_file_path)

        except OSError as error:
            self.write(Text(f"{Strings.read_error} {self.path}: {error}"))
            self.write(Strings.click_file_path)
