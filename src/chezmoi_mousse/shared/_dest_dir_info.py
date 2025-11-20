from enum import StrEnum
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import RichLog

from chezmoi_mousse import CanvasName, ReadCmd

from ._section_headers import SectionLabelText, SubSectionLabel

__all__ = ["DestDirInfo"]

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds


class LogText(StrEnum):
    add_dir_info = "Click a directary to see if it's managed or unmanaged."
    cat_prefix = "Click a file or directory in the tree to see the output from"
    diff_prefix = "Click a path to see the output from"
    dir_info = "Click a directary to see if it's managed or unmanaged."
    git_log_prefix = "Click a path in the tree to see the output from"
    in_dest_dir = "This is the destination directory (chezmoi destDir)"
    read_file = 'Click a file to see the output from "Path.read()".'
    cat = f'{cat_prefix} "{ReadCmd.cat.pretty_cmd}".'
    diff = f'{diff_prefix} "{ReadCmd.diff.pretty_cmd}".'
    diff_reverse = f'{diff_prefix} "{ReadCmd.diff_reverse.pretty_cmd}".'
    git_log_msg = f'{git_log_prefix} "{ReadCmd.git_log.pretty_cmd}".'


class DestDirInfo(VerticalGroup):

    dest_dir: "Path | None" = None

    def __init__(
        self,
        ids: "AppIds",
        contents_logger: bool = False,
        git_log: bool = False,
    ) -> None:
        self.ids = ids
        self.contents_logger = contents_logger
        self.git_log = git_log
        super().__init__(id=self.ids.container.dest_dir_info)

    def compose(self) -> ComposeResult:
        yield SubSectionLabel(SectionLabelText.path_info)
        yield RichLog(
            id=self.ids.logger.in_dest_dir, highlight=True, markup=False
        )

    def on_mount(self) -> None:
        rich_log = self.query_one(self.ids.logger.in_dest_dir_q, RichLog)
        rich_log.write(Text(LogText.in_dest_dir.value))
        if self.ids.canvas_name == CanvasName.add_tab:
            rich_log.write((Text(LogText.read_file.value)))
            rich_log.write(Text(LogText.dir_info.value))
            return
        elif (
            self.ids.canvas_name
            in (CanvasName.apply_tab, CanvasName.re_add_tab)
            and self.contents_logger is True
        ):
            rich_log.write(Text(LogText.cat.value))
            return
        elif (
            self.ids.canvas_name == CanvasName.apply_tab
            and self.git_log is False
        ):
            rich_log.write(Text(LogText.diff.value))
        elif (
            self.ids.canvas_name == CanvasName.re_add_tab
            and self.git_log is False
        ):
            rich_log.write(Text(LogText.diff_reverse.value))
            return
        rich_log.write(Text(LogText.git_log_msg.value))
