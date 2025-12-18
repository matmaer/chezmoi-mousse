from enum import StrEnum
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Label, RichLog, Static

from chezmoi_mousse import (
    AppType,
    DestDirStrings,
    NodeData,
    ReadCmd,
    SectionLabels,
    TabName,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["ContentsView"]


class ContentsTabStrings(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    empty_or_only_whitespace = "File is empty or contains only whitespace"
    managed_dir = "Managed directory:"
    output_from_cat = "File does not exist on disk, output from"
    output_from_read = "Output from Path.read"
    permission_denied = "Permission denied to read file"
    read_error = "Error reading path:"
    too_large = "File is larger than 150 KiB, truncating output for"
    truncated = "\n--- File content truncated to 150 KiB ---\n"
    unmanaged_dir = "Unmanaged directory:"


class ContentsInfo(VerticalGroup, AppType):
    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.contents_info)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.contents_info, classes=Tcss.sub_section_label
        )
        yield Static(id=self.ids.static.contents_info)


class ContentsView(Vertical, AppType):

    destDir: "Path | None" = None
    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.contents, classes=Tcss.border_title_top
        )
        self.click_file_info = (
            DestDirStrings.add
            if self.ids.canvas_name == TabName.add
            else DestDirStrings.cat
        )

    def compose(self) -> ComposeResult:
        yield ContentsInfo(ids=self.ids)
        yield Label(
            SectionLabels.file_read_output,
            classes=Tcss.sub_section_label,
            id=self.ids.label.file_read_output,
        )
        yield RichLog(
            id=self.ids.logger.contents,
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
        )

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        self.file_read_label = self.query_one(
            self.ids.label.file_read_output_q, Label
        )
        self.file_read_label.display = False
        self.contents_info = self.query_one(
            self.ids.container.contents_info_q, ContentsInfo
        )
        self.contents_info_static_text = self.contents_info.query_one(
            self.ids.static.contents_info_q, Static
        )
        if self.node_data is None:
            if self.ids.canvas_name == TabName.add:
                self.contents_info_static_text.update(DestDirStrings.add)
            elif self.ids.canvas_name == TabName.apply:
                self.contents_info_static_text.update(DestDirStrings.cat)
            elif self.ids.canvas_name == TabName.re_add:
                self.contents_info_static_text.update(DestDirStrings.re_add)

    def write_managed_directory(self, path_arg: "Path") -> None:
        if self.node_data is None:
            raise ValueError("node_data is None in ContentsView")
        self.rich_log.write(f"{ContentsTabStrings.managed_dir} {path_arg}")

    def watch_node_data(self) -> None:
        self.rich_log = self.query_one(self.ids.logger.contents_q, RichLog)
        if self.node_data is None:
            return
        else:
            dest_dir_info = self.query_one(
                self.ids.container.contents_info_q, ContentsInfo
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

        except OSError as error:
            self.rich_log.write(
                Text(
                    f"{ContentsTabStrings.read_error} {self.node_data.path}: {error}"
                )
            )
