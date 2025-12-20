from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Label, RichLog, Static

from chezmoi_mousse import (
    AppType,
    Chars,
    DestDirStrings,
    DiffCmdData,
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


class DiffInfo(VerticalGroup, AppType):
    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff_info)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabels.diff_info, classes=Tcss.sub_section_label)
        yield Static(id=self.ids.static.diff_info)


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
        yield Label(classes=Tcss.sub_section_label, id=self.ids.label.diff_cmd)
        yield RichLog(
            id=self.ids.logger.diff,
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
        )

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        self.diff_cmd_label = self.query_one(self.ids.label.diff_cmd_q, Label)
        self.diff_cmd_label.display = False
        self.diff_info_container = self.query_one(
            self.ids.container.diff_info_q, DiffInfo
        )
        self.diff_info_static_text = self.diff_info_container.query_one(
            self.ids.static.diff_info_q, Static
        )
        if self.node_data is None:
            self.diff_info_static_text.update(self.in_dest_dir_diff_msg)

    def get_diff_output(self) -> DiffCmdData:
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
            if (line.startswith("old mode") or line.startswith("new mode"))
        ]
        if self.node_data.path_kind == PathKind.DIR:
            dir_diff_lines = [
                line for line in diff_lines if line.startswith(("+++", "---"))
            ]
            for line in dir_diff_lines:
                if line.startswith("---") or line.startswith("+++"):
                    dir_diff_lines.append(line)
        elif self.node_data.path_kind == PathKind.FILE:
            file_diff_lines: list[str] = [
                line
                for line in diff_lines
                if line[0] in "+- " and not line.startswith(("+++", "---"))
            ]
            if len(file_diff_lines) == 0:
                file_diff_lines = ["The diff contains only whitespace."]

        diff_cmd_data = DiffCmdData(
            diff_cmd_label=diff_output.pretty_cmd,
            dir_diff_lines=dir_diff_lines,
            file_diff_lines=file_diff_lines,
            mode_diff_lines=mode_diff_lines,
        )
        if self.reverse is False:
            self.app.post_message(CurrentApplyDiffMsg(diff_cmd_data))
        else:
            self.app.post_message(CurrentReAddDiffMsg(diff_cmd_data))
        self.diff_cmd_label.display = True
        self.diff_cmd_label.update(diff_output.pretty_cmd)
        return diff_cmd_data

    def no_status_info_lines(self) -> list[str]:
        new_info_text: list[str] = []
        if self.node_data is None:
            return new_info_text
        new_info_text: list[str] = []
        # write lines for an unchanged file or directory
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
            self.diff_info_static_text.update("\n".join(new_info_text))
        return new_info_text

    def watch_node_data(self) -> None:
        if self.node_data is None:
            return

        self.diff_info_container.display = False
        self.diff_cmd_label.display = False
        self.rich_log = self.query_one(self.ids.logger.diff_q, RichLog)
        self.rich_log.clear()

        self.border_title = f" {self.node_data.path} "
        no_status_info: list[str] = self.no_status_info_lines()
        if len(no_status_info) > 0:
            self.diff_info_container.display = True
            self.diff_info_static_text.update("\n".join(no_status_info))
            return

        diff_cmd_data: DiffCmdData = self.get_diff_output()

        if len(diff_cmd_data.mode_diff_lines) > 0:
            self.diff_info_container.display = True
            lines: list[str] = []
            lines.append("Mode/permissions changes:")
            for line in diff_cmd_data.mode_diff_lines:
                lines.append(f" {Chars.bullet} {line}")
            self.diff_info_static_text.update("\n".join(lines))

        if self.node_data.path_kind == PathKind.DIR:
            self.diff_cmd_label.display = True
            for line in diff_cmd_data.dir_diff_lines:
                if line.startswith("---"):
                    self.rich_log.write(
                        Text(line, self.app.theme_variables["text-error"])
                    )
                elif line.startswith("+++"):
                    self.rich_log.write(
                        Text(line, self.app.theme_variables["text-success"])
                    )
            return

        if len(diff_cmd_data.file_diff_lines) > 0:
            self.diff_cmd_label.display = True
        for line in diff_cmd_data.file_diff_lines:
            if line.startswith("-"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-error"])
                )
            elif line.startswith("+"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-success"])
                )
