from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Static

from chezmoi_mousse import ReadCmd, SectionLabels, TabName

from ._section_headers import SubSectionLabel

__all__ = ["DestDirInfo"]

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds

ADD_DIR_INFO = "Click a directary to see if it's managed or unmanaged."
CAT_PREFIX = "Click a file or directory in the tree to see the output from"
DIFF_PREFIX = "Click a path to see the output from"
DIR_INFO = "Click a directary to see if it's managed or unmanaged."
GIT_LOG_PREFIX = "Click a path in the tree to see the output from"
IN_DEST_DIR = "This is the destination directory (chezmoi destDir)"


class DestDirStrings(StrEnum):
    read_file = (
        'Click a file to see the output from [$success]"Path.read()"[/].'
    )
    cat = f'{CAT_PREFIX} [$success]"{ReadCmd.cat.pretty_cmd}"[/].'
    diff = f'{DIFF_PREFIX} [$success]"{ReadCmd.diff.pretty_cmd}"[/].'
    diff_reverse = (
        f'{DIFF_PREFIX} [$success]"{ReadCmd.diff_reverse.pretty_cmd}"[/].'
    )
    git_log_msg = (
        f'{GIT_LOG_PREFIX} [$success]"{ReadCmd.git_log.pretty_cmd}"[/].'
    )


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
        yield SubSectionLabel(SectionLabels.path_info)

    def on_mount(self) -> None:
        lines: list[str] = []
        if self.ids.canvas_name == TabName.add:
            lines.append(DestDirStrings.read_file)
            lines.append(ADD_DIR_INFO)
        elif self.git_log is True:
            lines.append(DestDirStrings.git_log_msg)
        elif self.contents_logger is True:
            lines.append(DestDirStrings.cat)
        elif self.ids.canvas_name == TabName.apply:
            lines.append(DestDirStrings.diff)
        elif self.ids.canvas_name == TabName.re_add:
            lines.append(DestDirStrings.diff_reverse)
        self.mount(Static("\n".join(lines)))
