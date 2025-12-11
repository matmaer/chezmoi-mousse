from enum import StrEnum
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import RichLog, Static

from chezmoi_mousse import (
    AppType,
    DestDirStrings,
    NodeData,
    ReadCmd,
    SectionLabels,
    TabName,
    Tcss,
)

from ._section_headers import SubSectionLabel

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


class ContentsView(Vertical, AppType):

    destDir: "Path | None" = None
    # path: reactive["Path | None"] = reactive(None, init=False)
    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.contents, classes=Tcss.border_title_top
        )
        self.click_file_info = (
            DestDirStrings.read_file
            if self.ids.canvas_name == TabName.add
            else DestDirStrings.cat
        )

    def compose(self) -> ComposeResult:
        with Vertical(id=self.ids.container.dest_dir_info):
            yield SubSectionLabel(SectionLabels.path_info)
            yield Static(DestDirStrings.in_dest_dir)
            yield Static(self.click_file_info)
            yield Static(DestDirStrings.dir_info)
        yield RichLog(
            id=self.ids.logger.contents,
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
        )

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        self.rich_log = self.query_one(self.ids.logger.contents_q, RichLog)

    def write_managed_directory(self, path_arg: "Path") -> None:
        if self.node_data is None:
            raise ValueError("node_data is None in ContentsView")
        self.rich_log.write(f"{ContentsTabStrings.managed_dir} {path_arg}")
        self.rich_log.write(ContentsTabStrings.click_file_path)

    def watch_node_data(self) -> None:
        if self.node_data is None:
            return
        else:
            dest_dir_info = self.query_one(
                self.ids.container.dest_dir_info_q, Vertical
            )
            dest_dir_info.display = False
        self.border_title = f" {self.node_data.path} "
        self.rich_log.clear()
        truncated_message = ""
        try:
            if (
                self.node_data.path.is_file()
                and self.node_data.path.stat().st_size > 150 * 1024
            ):
                truncated_message = ContentsTabStrings.truncated
                self.rich_log.write(
                    f"{ContentsTabStrings.too_large} {self.node_data.path}"
                )
        except PermissionError as e:
            self.rich_log.write(e.strerror)
            self.rich_log.write(
                f"{ContentsTabStrings.permission_denied} {self.node_data.path}"
            )
            return

        try:
            with open(self.node_data.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if file_content.strip() == "":
                    self.rich_log.write(
                        ContentsTabStrings.empty_or_only_whitespace
                    )
                else:
                    self.rich_log.write(
                        f"{ContentsTabStrings.output_from_read} {self.node_data.path}\n"
                    )
                    self.rich_log.write(truncated_message + file_content)

        except UnicodeDecodeError:
            self.rich_log.write(
                f"{ContentsTabStrings.cannot_decode} {self.node_data.path}"
            )
            return

        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.node_data.path in self.app.chezmoi.dirs:
                self.write_managed_directory(self.node_data.path)
                return
            elif self.node_data.path in self.app.chezmoi.files:
                cat_output: "CommandResult" = self.app.chezmoi.read(
                    ReadCmd.cat, path_arg=self.node_data.path
                )
                self.rich_log.write(
                    f'{ContentsTabStrings.output_from_cat} "{cat_output.pretty_cmd}"\n'
                )
                if cat_output.std_out == "":
                    self.rich_log.write(
                        Text(
                            ContentsTabStrings.empty_or_only_whitespace,
                            style="dim",
                        )
                    )
                else:
                    self.rich_log.write(cat_output.std_out)
                return

        except IsADirectoryError:
            if self.node_data.path in self.app.chezmoi.dirs:
                self.write_managed_directory(self.node_data.path)
            else:
                self.rich_log.write(
                    f"{ContentsTabStrings.unmanaged_dir} {self.node_data.path}"
                )
                self.rich_log.write(ContentsTabStrings.click_file_path)

        except OSError as error:
            self.rich_log.write(
                Text(
                    f"{ContentsTabStrings.read_error} {self.node_data.path}: {error}"
                )
            )
            self.rich_log.write(ContentsTabStrings.click_file_path)
