from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse import (
    AppType,
    DiffData,
    OperateStrings,
    PathKind,
    ReadCmd,
    SectionLabels,
    TabName,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult, NodeData

__all__ = ["DiffView"]


class DiffStrings(StrEnum):
    contains_status_paths = (
        "Directory contains the following paths with a status (recursive)"
    )
    no_dir_status = "No diff available, the directory has no status."
    no_file_status = "No diff available, the file has no status."
    truncated = "\n--- Diff output truncated to 1000 lines ---\n"


class DiffInfo(VerticalGroup):

    info_lines: reactive[list[Static] | None] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff_info)

    def compose(self) -> ComposeResult:
        yield Label(SectionLabels.diff_info, classes=Tcss.sub_section_label)
        yield ScrollableContainer(id=self.ids.container.diff_info)

    def on_mount(self) -> None:
        self.query_one(
            self.ids.container.diff_info_q, ScrollableContainer
        ).mount(Static(OperateStrings.in_dest_dir_click_path))
        self.label = self.query_exactly_one(Label)

    def watch_info_lines(self) -> None:
        if self.info_lines is None:
            return
        self.label.update(DiffStrings.contains_status_paths)
        diff_info = self.query_one(
            self.ids.container.diff_info_q, ScrollableContainer
        )
        diff_info.remove_children()
        diff_info.mount_all([Static(" ")] + self.info_lines)


class DiffLines(VerticalGroup):

    diff_data: reactive[DiffData | None] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff_lines)

    def compose(self) -> ComposeResult:
        yield Label(classes=Tcss.sub_section_label)
        yield ScrollableContainer(id=self.ids.container.diff_output)

    def on_mount(self) -> None:
        self.display = False
        self.label = self.query_exactly_one(Label)

    def watch_diff_data(self) -> None:
        if self.diff_data is None:
            return
        self.label.update(self.diff_data.diff_cmd_label)
        diff_output = self.query_one(
            self.ids.container.diff_output_q, ScrollableContainer
        )
        diff_output.remove_children()
        diff_output.mount_all(self.diff_data.diff_lines)


class DiffView(Vertical, AppType):

    destDir: "Path | None" = None
    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.diff, classes=Tcss.border_title_top
        )
        if self.ids.canvas_name == TabName.re_add:
            self.diff_cmd = ReadCmd.diff_reverse
        else:
            self.diff_cmd = ReadCmd.diff

    def compose(self) -> ComposeResult:
        yield DiffInfo(ids=self.ids)
        yield DiffLines(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = f" {self.destDir} "
        self.diff_lines = self.query_one(
            self.ids.container.diff_lines_q, DiffLines
        )

    def create_diff_data(self) -> DiffData:
        static_list: list[Static] = []
        if self.node_data is None:
            raise ValueError("node_data is None")
        diff_output: "CommandResult" = self.app.cmd.read(
            self.diff_cmd, path_arg=self.node_data.path
        )
        diff_lines = diff_output.std_out.splitlines()
        mode_lines = [
            line
            for line in diff_lines
            if line.startswith(("old", "new", "changed", "deleted"))
        ]
        if len(mode_lines) > 0:
            for line in mode_lines:
                if line.startswith(("old", "deleted")):
                    static_list.append(
                        Static(line, classes=Tcss.style_removed)
                    )
                elif line.startswith("new"):
                    static_list.append(Static(line, classes=Tcss.style_added))
                    diff_lines.remove(line)
                elif line.startswith("changed"):
                    static_list.append(
                        Static(line, classes=Tcss.style_changed)
                    )
            static_list.append(Static(""))
        path_lines = [
            line for line in diff_lines if line.startswith(("+++", "---"))
        ]
        if len(path_lines) > 0:
            for line in path_lines:
                if line.startswith("---"):
                    static_list.append(
                        Static(line, classes=Tcss.style_removed)
                    )
                elif line.startswith("+++"):
                    static_list.append(Static(line, classes=Tcss.style_added))
            static_list.append(Static(""))
        file_lines = [
            line
            for line in diff_lines
            if line.startswith(("+", "-", " "))
            and not line.startswith(("+++", "---"))
        ]
        # TODO: make lines limit configurable, look into paging,
        # temporary solution
        lines_limit = 1000
        lines = 0
        for line in file_lines:
            if line.startswith("-"):
                static_list.append(Static(line, classes=Tcss.style_removed))
            elif line.startswith("+"):
                static_list.append(Static(line, classes=Tcss.style_added))
            elif line.startswith(" "):
                static_list.append(Static(line, classes=Tcss.style_context))
            lines += 1
            if lines >= lines_limit:
                static_list.append(Static(" "))
                static_list.append(Static(DiffStrings.truncated))
                break
        diff_data = DiffData(
            diff_cmd_label=diff_output.pretty_cmd, diff_lines=static_list
        )
        return diff_data

    def watch_node_data(self) -> None:
        if self.node_data is None or self.destDir is None:
            return
        diff_info = self.query_one(self.ids.container.diff_info_q, DiffInfo)
        diff_info.display = False
        self.diff_lines.display = False
        self.border_title = (
            f" {self.node_data.path.relative_to(self.destDir)} "
        )
        diff_data: DiffData = self.create_diff_data()

        info_lines: list[Static] = []
        if (
            self.node_data.path_kind == PathKind.FILE
            and self.node_data.path not in self.app.paths.status_files
        ):
            diff_info.display = True
            diff_info.info_lines = [
                Static(f"Managed file [$text-accent]{self.node_data.path}[/]"),
                Static(f"{DiffStrings.no_file_status}"),
            ]
        elif (
            self.node_data.path_kind == PathKind.FILE
            and self.node_data.path in self.app.paths.status_files
        ):
            diff_info.display = False
            self.diff_lines.display = True
            self.diff_lines.diff_data = diff_data
            return

        # Handle directory status paths
        status_paths = (
            self.app.paths.list_apply_status_paths_in(self.node_data.path)
            if self.ids.canvas_name == TabName.apply
            else self.app.paths.list_re_add_status_paths_in(
                self.node_data.path
            )
        )
        for path, status in status_paths.items():
            if status == "A":
                info_lines.append(
                    Static(f"{path} (Added)", classes=Tcss.style_added)
                )
            elif status == "D":
                info_lines.append(
                    Static(f"{path} (Deleted)", classes=Tcss.style_removed)
                )
            elif status == "M":
                info_lines.append(
                    Static(f"{path} (Modified)", classes=Tcss.style_changed)
                )
            elif status == " ":
                info_lines.append(
                    Static(f"{path} (Unchanged)", classes=Tcss.style_unchanged)
                )
            else:
                info_lines.append(Static(f"{path} ({status})"))
        diff_info.display = True
        diff_info.info_lines = info_lines

        if (
            self.node_data.path_kind == PathKind.DIR
            and self.node_data.path not in self.app.paths.status_dirs
        ):
            info_lines.append(
                Static(
                    f"Managed directory [$text-accent]{self.node_data.path}[/]."
                )
            )
            info_lines.append(Static(f"{DiffStrings.no_dir_status}"))

        if len(diff_data.diff_lines) > 0:
            self.diff_lines.display = True
            self.diff_lines.diff_data = diff_data
