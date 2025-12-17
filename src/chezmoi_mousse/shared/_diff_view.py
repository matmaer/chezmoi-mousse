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
    PathKind,
    ReadCmd,
    SectionLabels,
    Tcss,
)

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
        # yield Label(
        #     SectionLabels.diff_file_output,
        #     classes=Tcss.sub_section_label,
        #     id=self.ids.label.diff_file_output,
        # )


class DiffView(Vertical, AppType):

    destDir: "Path | None" = None
    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds", reverse: bool) -> None:
        self.ids = ids
        self.reverse = reverse
        self.diff_cmd: ReadCmd = (
            ReadCmd.diff_reverse if self.reverse else ReadCmd.diff
        )
        self.in_dest_dir_diff_msg = (
            DestDirStrings.diff_reverse
            if self.reverse
            else DestDirStrings.diff
        )
        super().__init__(
            id=self.ids.container.diff, classes=Tcss.border_title_top
        )

    def compose(self) -> ComposeResult:
        yield DiffInfo(ids=self.ids)
        yield Label(
            SectionLabels.diff_file_output,
            classes=Tcss.sub_section_label,
            id=self.ids.label.diff_file_output,
        )
        yield Label(
            SectionLabels.diff_dir_output,
            classes=Tcss.sub_section_label,
            id=self.ids.label.diff_dir_output,
        )
        yield RichLog(
            id=self.ids.logger.diff,
            auto_scroll=False,
            highlight=True,
            wrap=True,  # TODO: implement footer binding to toggle wrap
        )

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        self.diff_info = self.query_one(
            self.ids.container.diff_info_q, DiffInfo
        )
        self.diff_info_static_text = self.diff_info.query_one(
            self.ids.static.diff_info_q, Static
        )
        self.diff_info_static_text.update(
            "\n".join([DestDirStrings.in_dest_dir, self.in_dest_dir_diff_msg])
        )
        self.dir_output_label = self.query_one(
            self.ids.label.diff_dir_output_q, Label
        )
        self.dir_output_label.display = False
        self.file_output_label = self.query_one(
            self.ids.label.diff_file_output_q, Label
        )
        self.file_output_label.display = False

    def watch_node_data(self) -> None:
        if self.node_data is None:
            return
        if (
            self.node_data.path not in self.app.chezmoi.files
            and self.node_data.path not in self.app.chezmoi.dirs
        ):
            raise ValueError(
                f"{self.node_data.path} is not managed but shown."
            )
        new_info_text: list[str] = []
        self.dir_output_label.display = False
        self.file_output_label.display = False
        self.border_title = f" {self.node_data.path} "
        self.rich_log = self.query_one(self.ids.logger.diff_q, RichLog)
        self.rich_log.clear()

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
            self.diff_info_static_text.update("\n".join(new_info_text))
            return

        if (
            self.node_data.path_kind == PathKind.FILE
            and self.node_data.path not in self.app.chezmoi.status_files
        ):
            new_info_text.append(
                f"Managed file [$text-accent]{self.node_data.path}[/]."
            )
            new_info_text.append("No diff available, the file has no status.")
            self.diff_info_static_text.update("\n".join(new_info_text))
            return

        # create the diff view for a changed file
        diff_output: "CommandResult" = self.app.chezmoi.read(
            self.diff_cmd, path_arg=self.node_data.path
        )
        diff_lines = diff_output.std_out.splitlines()
        new_info_text.append(
            f"Executed command [$text-success]{diff_output.pretty_cmd}[/]"
        )
        mode_diff_lines = [
            line
            for line in diff_lines
            if (line.startswith("old mode") or line.startswith("new mode"))
        ]
        if len(mode_diff_lines) > 0:
            new_info_text.append("Permissions/mode will be changed.")
        for line in mode_diff_lines:
            new_info_text.append(f" {Chars.bullet} {line}")

        if self.node_data.path_kind == PathKind.DIR:
            dir_diff_lines = [
                line for line in diff_lines if line.startswith(("+++", "---"))
            ]
            self.dir_output_label.display = True
            for line in dir_diff_lines:
                if line.startswith("---"):
                    self.rich_log.write(
                        Text(line, self.app.theme_variables["text-error"])
                    )
                elif line.startswith("+++"):
                    self.rich_log.write(
                        Text(line, self.app.theme_variables["text-success"])
                    )
            self.diff_info_static_text.update("\n".join(new_info_text))
            return

        self.diff_info_static_text.update("\n".join(new_info_text))
        file_diff_lines: list[str] = [
            line
            for line in diff_lines
            if line[0] in "+- " and not line.startswith(("+++", "---"))
        ]
        if len(file_diff_lines) > 0:
            self.file_output_label.display = True
        for line in file_diff_lines:
            if line.startswith("-"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-error"])
                )
            elif line.startswith("+"):
                self.rich_log.write(
                    Text(line, self.app.theme_variables["text-success"])
                )
