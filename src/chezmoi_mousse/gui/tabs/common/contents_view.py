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
    PathKind,
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
    empty_or_only_whitespace = "File is empty or contains only whitespace."
    managed_dir = "Managed directory "
    output_from_cat = "File does not exist on disk, output from "
    permission_denied = "Permission denied to read file "
    read_error = "Error reading path "
    truncated = "\n--- File content truncated to "
    unmanaged_dir = "Unmanaged directory "


class ContentsInfo(VerticalGroup, AppType):
    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.contents_info)

    def compose(self) -> ComposeResult:
        yield Label(
            SectionLabels.contents_info,
            classes=Tcss.sub_section_label,
            id=self.ids.label.contents_info,
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

    def compose(self) -> ComposeResult:
        yield ContentsInfo(ids=self.ids)
        yield Label(
            SectionLabels.cat_config_output,
            classes=Tcss.sub_section_label,
            id=self.ids.label.cat_config_output,
        )
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
        # TODO: make this configurable but should be reasonable truncate for
        # displaying enough of a file to judge operating on it.
        self.truncate_size = self.app.max_file_size // 10
        self.border_title = f" {self.destDir} "
        self.cat_config_label = self.query_one(
            self.ids.label.cat_config_output_q, Label
        )
        self.cat_config_label.display = False
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
        if self.ids.canvas_name == TabName.add:
            self.contents_info_static_text.update(DestDirStrings.add)
        elif self.ids.canvas_name == TabName.apply:
            self.contents_info_static_text.update(DestDirStrings.cat)
        elif self.ids.canvas_name == TabName.re_add:
            self.contents_info_static_text.update(DestDirStrings.re_add)

    def open_file_and_update_ui(self, file_path: "Path") -> None:
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.contents_info_static_text.update(
                    ContentsTabStrings.empty_or_only_whitespace
                )
                return
            with open(file_path, "rt", encoding="utf-8") as f:
                f_contents = f.read(self.truncate_size)
            if f_contents.strip() == "":
                self.contents_info_static_text.update(
                    ContentsTabStrings.empty_or_only_whitespace
                )
                return
            self.file_read_label.display = True
            self.rich_log.write(f_contents)
            if file_size > self.truncate_size:
                self.rich_log.write(
                    f"{ContentsTabStrings.truncated} {self.truncate_size / 1024} KiB ---"
                )
        except PermissionError as error:
            self.contents_info_static_text.update(
                f"{ContentsTabStrings.permission_denied}{file_path}"
            )
            self.rich_log.write(error.strerror)
            return
        except UnicodeDecodeError:
            self.contents_info_static_text.update(
                f"{ContentsTabStrings.cannot_decode}{file_path}"
            )
        except OSError as error:
            self.contents_info_static_text.update(
                f"{ContentsTabStrings.read_error}{file_path}: {error}"
            )
            self.rich_log.write(error.strerror)

    def write_cat_output(self, file_path: "Path") -> None:
        if file_path in self.app.cmd.paths.files:
            self.cat_config_label.display = True
            cat_output: "CommandResult" = self.app.cmd.read(
                ReadCmd.cat, path_arg=file_path
            )
            self.contents_info_static_text.update(
                f"{ContentsTabStrings.output_from_cat}[$text-success]{cat_output.pretty_cmd}[/]"
            )
            if cat_output.std_out.strip() == "":
                self.rich_log.write(
                    Text(
                        ContentsTabStrings.empty_or_only_whitespace,
                        style="dim",
                    )
                )
            else:
                self.rich_log.write(cat_output.std_out)

    def write_dir_info(self, dir_path: "Path") -> None:
        if dir_path in self.app.cmd.paths.dirs:
            self.contents_info_static_text.update(
                f"{ContentsTabStrings.managed_dir}[$text-accent]{dir_path}[/]"
            )
        else:
            self.contents_info_static_text.update(
                f"{ContentsTabStrings.unmanaged_dir}[$text-accent]{dir_path}[/]"
            )
        return

    def watch_node_data(self) -> None:
        if self.node_data is None or self.destDir is None:
            return
        self.border_title = (
            f" {self.node_data.path.relative_to(self.destDir)} "
        )
        self.cat_config_label.display = False
        self.file_read_label.display = False
        self.rich_log = self.query_one(self.ids.logger.contents_q, RichLog)
        self.rich_log.clear()

        if self.node_data.path_kind == PathKind.DIR:
            self.contents_info.display = True
            self.write_dir_info(self.node_data.path)
            return
        elif self.node_data.path_kind == PathKind.FILE:
            self.contents_info.display = False
            if self.node_data.found is True:
                self.open_file_and_update_ui(self.node_data.path)
            elif self.node_data.found is False:
                self.write_cat_output(self.node_data.path)
            else:
                self.app.notify(
                    "Unexpected condition in ContentsView.watch_node_data"
                )
