from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
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

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult, NodeData

__all__ = ["DiffLines", "DiffView"]


class DiffStrings(StrEnum):
    contains_status_paths = "Contains status paths:"
    no_dir_status = "No diff available, the directory has no status."
    no_file_status = "No diff available, the file has no status."
    truncacted = "\n--- Diff output truncated to 1000 lines ---\n"


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
        yield ScrollableContainer(id=self.ids.container.diff_output)

    def watch_diff_data(self) -> None:
        if self.diff_data is None:
            return
        diff_cmd_label = self.query_one(self.ids.label.diff_cmd_q, Label)
        diff_cmd_label.update(self.diff_data.diff_cmd_label)
        diff_output = self.query_one(
            self.ids.container.diff_output_q, ScrollableContainer
        )
        diff_output.remove_children()
        static_list: list[Static] = []
        for line in self.diff_data.mode_diff_lines:
            if line.startswith(("old mode", "deleted file mode")):
                static_list.append(
                    Static(
                        f"{Chars.bullet} {line}",
                        classes=Tcss.diff_line_removed,
                    )
                )
            elif line.startswith(("new mode", "new file mode")):
                static_list.append(
                    Static(
                        f"{Chars.bullet} {line}", classes=Tcss.diff_line_added
                    )
                )
            elif line.startswith("changed mode"):
                static_list.append(
                    Static(
                        f"{Chars.bullet} {line}",
                        classes=Tcss.diff_line_changed_mode,
                    )
                )
            static_list.append(Static(""))  # empty line after mode lines
        # TODO: make lines limit configurable, look into paging,
        # temporary solution
        lines_limit = 1000
        lines = 0
        for line in (
            self.diff_data.dir_diff_lines + self.diff_data.file_diff_lines
        ):
            if line.startswith("+"):
                static_list.append(Static(line, classes=Tcss.diff_line_added))
            elif line.startswith("-"):
                static_list.append(
                    Static(line, classes=Tcss.diff_line_removed)
                )
            elif line.startswith(" "):
                static_list.append(
                    Static(
                        f"{Chars.bullet}{line[1:]}",
                        classes=Tcss.diff_line_context,
                    )
                )
            lines += 1
            if lines >= lines_limit:
                static_list.append(Static(DiffStrings.truncacted))
                break
        diff_output.mount_all(static_list)


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

    def run_chezmoi_diff(self) -> DiffData:
        if self.node_data is None:
            raise ValueError("node_data is None")
        mode_diff_lines: list[str] = []
        dir_diff_lines: list[str] = []
        file_diff_lines: list[str] = []
        diff_output: "CommandResult" = self.app.cmd.read(
            self.diff_cmd, path_arg=self.node_data.path
        )
        diff_lines = diff_output.std_out.splitlines()
        mode_diff_lines = [
            line
            for line in diff_lines
            if line.startswith(
                (
                    "changed mode",
                    "deleted file mode",
                    "new file mode",
                    "new mode",
                    "old mode",
                )
            )
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

    def watch_node_data(self) -> None:
        if self.node_data is None or self.destDir is None:
            return

        diff_info = self.query_one(self.ids.container.diff_info_q, DiffInfo)
        diff_info.display = False
        diff_lines = self.query_one(self.ids.container.diff_lines_q, DiffLines)
        diff_lines.display = False

        self.border_title = (
            f" {self.node_data.path.relative_to(self.destDir)} "
        )
        diff_data: DiffData = self.run_chezmoi_diff()

        info_lines: list[str] = []
        if (
            self.node_data.path_kind == PathKind.FILE
            and self.node_data.path not in self.app.cmd.paths.status_files
        ):
            diff_info.display = True
            diff_info.info_lines = [
                f"Managed file [$text-accent]{self.node_data.path}[/]",
                f"{DiffStrings.no_file_status}",
            ]
        elif (
            self.node_data.path_kind == PathKind.FILE
            and self.node_data.path in self.app.cmd.paths.status_files
        ):
            diff_info.display = False
            diff_lines.display = True
            diff_lines.diff_data = diff_data
            return
        # Handle directory status paths
        status_paths = (
            self.app.cmd.paths.list_apply_status_paths_in(self.node_data.path)
            if self.reverse is False
            else self.app.cmd.paths.list_re_add_status_paths_in(
                self.node_data.path
            )
        )
        to_show: list[tuple["Path", str]] = []
        if len(status_paths) > 0:
            to_show = [
                (path, status)
                for path, status in status_paths.items()
                if status != " " and path != self.node_data.path
            ]
        if len(to_show) > 0:
            info_lines.append(f"{DiffStrings.contains_status_paths}")
            for path, status in to_show:
                info_lines.append(f"  {path} ({status})")
            diff_info.display = True
            diff_info.info_lines = info_lines

        if (
            self.node_data.path_kind == PathKind.DIR
            and self.node_data.path not in self.app.cmd.paths.status_dirs
        ):
            info_lines.append(
                f"Managed directory [$text-accent]{self.node_data.path}[/]."
            )
            info_lines.append(f"{DiffStrings.no_dir_status}")

        if (
            len(diff_data.file_diff_lines) > 0
            or len(diff_data.dir_diff_lines) > 0
        ):
            diff_lines.display = True
            diff_lines.diff_data = diff_data
