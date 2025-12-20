from typing import TYPE_CHECKING

# from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import (
    AppType,
    Chars,
    DestDirStrings,
    DiffData,
    PathKind,
    ReadCmd,
    SectionLabels,
    Tcss,
)

from ._messages import CurrentApplyDiffMsg, CurrentReAddDiffMsg

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, AppType, CommandResult, NodeData

__all__ = ["DiffView"]


class DiffInfo(VerticalGroup):

    info_lines: reactive[list[str] | None] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff_info)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabels.diff_info, classes=Tcss.sub_section_label)
        yield Static(id=self.ids.static.diff_info)

    def watch_info_lines(self) -> None:
        if self.info_lines is None:
            return
        static_widget = self.query_one(self.ids.static.diff_info_q, Static)
        static_widget.update("\n".join(self.info_lines))


class DiffLines(VerticalGroup):

    diff_data: reactive["DiffData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff_lines)

    def compose(self) -> ComposeResult:
        yield Label(id=self.ids.label.diff_cmd, classes=Tcss.sub_section_label)
        yield Static(id=self.ids.static.diff_lines)

    def watch_diff_data(self) -> None:
        if self.diff_data is None:
            return
        diff_cmd_label = self.query_one(self.ids.label.diff_cmd_q, Label)
        diff_cmd_label.update(self.diff_data.diff_cmd_label)
        static_widget = self.query_one(self.ids.static.diff_lines_q, Static)
        to_write: list[str] = []
        for line in self.diff_data.mode_diff_lines:
            if line.startswith("old mode"):
                to_write.append(f" {Chars.bullet} {line}")
        for line in self.diff_data.dir_diff_lines:
            if line.startswith("+++"):
                to_write.append(f"[$text-success on $success-muted]{line}[/]")
            elif line.startswith("---"):
                to_write.append(f"[$text-error on $error-muted]{line}[/]")
        for line in self.diff_data.file_diff_lines:
            if line.startswith("+"):
                to_write.append(f"[$text-success on $success-muted]{line}[/]")
            elif line.startswith("-"):
                to_write.append(f"[$text-error on $error-muted]{line}[/]")
        static_widget.update("\n".join(to_write))


class DiffView(Vertical, AppType):

    destDir: "Path | None" = None
    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds", reverse: bool) -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.diff, classes=Tcss.border_title_top
        )
        self.reverse = reverse
        if self.reverse is True:
            self.diff_cmd = ReadCmd.diff_reverse
            self.in_dest_dir_diff_msg = DestDirStrings.diff_reverse
        else:
            self.diff_cmd = ReadCmd.diff
            self.in_dest_dir_diff_msg = DestDirStrings.diff

    def compose(self) -> ComposeResult:
        yield DiffInfo(ids=self.ids)
        yield DiffLines(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        diff_info = self.query_one(self.ids.container.diff_info_q, DiffInfo)
        diff_lines = self.query_one(self.ids.container.diff_lines_q, DiffLines)
        diff_lines.display = False
        if self.node_data is None:
            diff_info.info_lines = [self.in_dest_dir_diff_msg]

    def create_diff_data(self) -> DiffData:
        if self.node_data is None:
            raise ValueError("node_data is None")
        mode_diff_lines: list[str] = []
        dir_diff_lines: list[str] = []
        file_diff_lines: list[str] = []
        diff_output: "CommandResult" = self.app.chezmoi.read(
            self.diff_cmd, path_arg=self.node_data.path
        )
        diff_lines = diff_output.std_out.splitlines()
        mode_diff_lines = [
            line
            for line in diff_lines
            if line.startswith(("new mode", "old mode"))
        ]
        if self.node_data.path_kind == PathKind.DIR:
            dir_diff_lines.extend(
                [
                    line
                    for line in diff_lines
                    if line.startswith(("+++", "---"))
                ]
            )
        elif self.node_data.path_kind == PathKind.FILE:
            file_diff_lines.extend(
                [
                    line
                    for line in diff_lines
                    if line[0] in "+- " and not line.startswith(("+++", "---"))
                ]
            )

        diff_data = DiffData(
            diff_cmd_label=diff_output.pretty_cmd,
            dir_diff_lines=dir_diff_lines,
            file_diff_lines=file_diff_lines,
            mode_diff_lines=mode_diff_lines,
        )
        return diff_data

    def no_status_info_lines(self) -> list[str]:
        if self.node_data is None:
            raise ValueError("node_data is None")
        new_info_text: list[str] = []
        # lines for an unchanged file or directory
        if (
            self.node_data.path_kind == PathKind.DIR
            and self.node_data.path not in self.app.chezmoi.status_dirs
        ):
            new_info_text.append(
                f"Managed directory [$text-accent]{self.node_data.path}[/]."
            )
            new_info_text.append(
                "No diff available, the directory has no status."
            )
        elif (
            self.node_data.path_kind == PathKind.FILE
            and self.node_data.path not in self.app.chezmoi.status_files
        ):
            new_info_text.append(
                f"Managed file [$text-accent]{self.node_data.path}[/]."
            )
            new_info_text.append("No diff available, the file has no status.")
        return new_info_text

    def watch_node_data(self) -> None:
        if self.node_data is None:
            return

        diff_info = self.query_one(self.ids.container.diff_info_q, DiffInfo)
        diff_info.display = False
        diff_lines = self.query_one(self.ids.container.diff_lines_q, DiffLines)
        diff_lines.display = False

        self.border_title = f" {self.node_data.path} "

        no_status_info: list[str] = self.no_status_info_lines()
        if len(no_status_info) > 0:
            diff_info.display = True
            diff_info.info_lines = no_status_info
            return

        diff_data: DiffData = self.create_diff_data()
        if self.reverse is False:
            self.app.post_message(CurrentApplyDiffMsg(diff_data))
        else:
            self.app.post_message(CurrentReAddDiffMsg(diff_data))
        diff_lines.display = True
        diff_lines.diff_data = diff_data
