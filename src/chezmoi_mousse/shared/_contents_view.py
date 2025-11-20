from enum import StrEnum
from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import RichLog

from chezmoi_mousse import AppType, ReadCmd, Tcss

from ._dest_dir_info import DestDirInfo

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["ContentsView"]


class ContentsTabStrings(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    click_file_path = "Click a file path in the tree to see the contents."
    empty_or_only_whitespace = "File is empty or contains only whitespace"
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

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.logger.contents,
            auto_scroll=False,
            wrap=True,  # TODO: implement footer binding to toggle wrap
            highlight=True,
            classes=Tcss.border_title_top.name,
        )

    def on_mount(self) -> None:
        self.mount(DestDirInfo(ids=self.ids, contents_logger=True))

    def write_managed_directory(self) -> None:
        self.write(f"{ContentsTabStrings.managed_dir} {self.path}")
        self.write(ContentsTabStrings.click_file_path)

    def watch_path(self) -> None:
        if self.path is None:
            return
        else:
            dest_dir_info = self.query_one(
                self.ids.container.dest_dir_info_q, DestDirInfo
            )
            dest_dir_info.visible = False
        self.border_title = f" {self.path} "
        self.clear()
        truncated_message = ""
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated_message = ContentsTabStrings.truncated
                self.write(f"{ContentsTabStrings.too_large} {self.path}")
        except PermissionError as e:
            self.write(e.strerror)
            self.write(f"{ContentsTabStrings.permission_denied} {self.path}")
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if file_content.strip() == "":
                    self.write(ContentsTabStrings.empty_or_only_whitespace)
                else:
                    self.write(
                        f"{ContentsTabStrings.output_from_read} {self.path}\n"
                    )
                    self.write(truncated_message + file_content)

        except UnicodeDecodeError:
            self.write(f"{ContentsTabStrings.cannot_decode} {self.path}")
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
                    f'{ContentsTabStrings.output_from_cat} "{cat_output.pretty_cmd}"\n'
                )
                if cat_output.std_out == "":
                    self.write(
                        Text(
                            ContentsTabStrings.empty_or_only_whitespace,
                            style="dim",
                        )
                    )
                else:
                    self.write(cat_output.std_out)
                return

        except IsADirectoryError:
            if self.path in self.app.chezmoi.dirs:
                self.write_managed_directory()
            else:
                self.write(f"{ContentsTabStrings.unmanaged_dir} {self.path}")
                self.write(ContentsTabStrings.click_file_path)

        except OSError as error:
            self.write(
                Text(f"{ContentsTabStrings.read_error} {self.path}: {error}")
            )
            self.write(ContentsTabStrings.click_file_path)
