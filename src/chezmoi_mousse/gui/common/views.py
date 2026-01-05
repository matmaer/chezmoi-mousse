from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.widgets import DataTable, Label, RichLog, Static

from chezmoi_mousse import (
    AppType,
    DiffData,
    NodeData,
    OperateStrings,
    PathKind,
    ReadCmd,
    SectionLabels,
    StatusCode,
    TabName,
    Tcss,
)

if TYPE_CHECKING:

    from chezmoi_mousse import AppIds, CommandResult, NodeData

    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable

__all__ = ["ContentsView", "DiffView", "GitLogPath", "GitLogGlobal"]


class ContentsView(Vertical, AppType):

    class ContentStr(StrEnum):
        cannot_decode = "Path cannot be decoded as UTF-8:"
        empty_or_only_whitespace = "File is empty or contains only whitespace."
        managed_dir = "Managed directory "
        output_from_cat = "File does not exist on disk, output from "
        permission_denied = "Permission denied to read file "
        read_error = "Error reading path "
        truncated = "\n--- File content truncated to "
        unmanaged_dir = "Unmanaged directory "

    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.contents, classes=Tcss.border_title_top
        )

    def compose(self) -> ComposeResult:
        yield VerticalGroup(
            Label(
                SectionLabels.contents_info,
                classes=Tcss.sub_section_label,
                id=self.ids.label.contents_info,
            ),
            Static(id=self.ids.static.contents_info),
            id=self.ids.container.contents_info,
        )
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
        self.border_title = f" {self.app.dest_dir} "
        self.cat_config_label = self.query_one(
            self.ids.label.cat_config_output_q, Label
        )
        self.cat_config_label.display = False
        self.file_read_label = self.query_one(
            self.ids.label.file_read_output_q, Label
        )
        self.file_read_label.display = False
        self.contents_info = self.query_one(
            self.ids.container.contents_info_q, VerticalGroup
        )
        self.contents_info_static_text = self.contents_info.query_one(
            self.ids.static.contents_info_q, Static
        )
        self.contents_info_static_text.update(
            OperateStrings.in_dest_dir_click_path
        )

    def open_file_and_update_ui(self, file_path: Path) -> None:
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.contents_info_static_text.update(
                    self.ContentStr.empty_or_only_whitespace
                )
                return
            with open(file_path, "rt", encoding="utf-8") as f:
                f_contents = f.read(self.truncate_size)
            if f_contents.strip() == "":
                self.contents_info_static_text.update(
                    self.ContentStr.empty_or_only_whitespace
                )
                return
            self.file_read_label.display = True
            self.rich_log.write(f_contents)
            if file_size > self.truncate_size:
                self.rich_log.write(
                    f"{self.ContentStr.truncated} {self.truncate_size / 1024} KiB ---"
                )
        except PermissionError as error:
            self.contents_info_static_text.update(
                f"{self.ContentStr.permission_denied}{file_path}"
            )
            self.rich_log.write(error.strerror)
            return
        except UnicodeDecodeError:
            self.contents_info_static_text.update(
                f"{self.ContentStr.cannot_decode}{file_path}"
            )
        except OSError as error:
            self.contents_info_static_text.update(
                f"{self.ContentStr.read_error}{file_path}: {error}"
            )
            self.rich_log.write(error.strerror)

    def write_cat_output(self, file_path: Path) -> None:
        if file_path in self.app.paths.files:
            self.cat_config_label.display = True
            cat_output: "CommandResult" = self.app.cmd.read(
                ReadCmd.cat, path_arg=file_path
            )
            self.contents_info_static_text.update(
                f"{self.ContentStr.output_from_cat}[$text-success]{cat_output.pretty_cmd}[/]"
            )
            if cat_output.std_out.strip() == "":
                self.rich_log.write(
                    Text(self.ContentStr.empty_or_only_whitespace, style="dim")
                )
            else:
                self.rich_log.write(cat_output.std_out)

    def write_dir_info(self, dir_path: Path) -> None:
        if dir_path in self.app.paths.dirs:
            self.contents_info_static_text.update(
                f"{self.ContentStr.managed_dir}[$text-accent]{dir_path}[/]"
            )
        else:
            self.contents_info_static_text.update(
                f"{self.ContentStr.unmanaged_dir}[$text-accent]{dir_path}[/]"
            )
        return

    def watch_node_data(self) -> None:
        if self.node_data is None:
            return
        if self.app.dest_dir is None:
            raise ValueError(
                "self.app.dest_dir is None in ContentsView.watch_node_data"
            )
        self.border_title = (
            f" {self.node_data.path.relative_to(self.app.dest_dir)} "
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
        self.border_title = f" {self.app.dest_dir} "
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
        if self.node_data is None:
            return
        diff_info = self.query_one(self.ids.container.diff_info_q, DiffInfo)
        diff_info.display = False
        self.diff_lines.display = False
        if self.app.dest_dir is None:
            raise ValueError(
                "self.app.dest_dir is None in DiffView.watch_node_data"
            )
        self.border_title = (
            f" {self.node_data.path.relative_to(self.app.dest_dir)} "
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
            if status == StatusCode.Added:
                info_lines.append(
                    Static(f"{path} (Added)", classes=Tcss.style_added)
                )
            elif status == StatusCode.Deleted:
                info_lines.append(
                    Static(f"{path} (Deleted)", classes=Tcss.style_removed)
                )
            elif status == StatusCode.Modified:
                info_lines.append(
                    Static(f"{path} (Modified)", classes=Tcss.style_changed)
                )
            elif status == StatusCode.No_Change:
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


class GitLogDataTable(DataTable[Text], AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.datatable.git_log)

    def on_mount(self) -> None:
        self.row_color = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        self.add_row(*row)

    def populate_datatable(self, command_result: "CommandResult") -> None:
        if (
            command_result.exit_code != 0
            or not command_result.std_out.splitlines()
        ):
            return
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
        for line in command_result.std_out.splitlines():
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, self.row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, self.row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, self.row_color["error"])
            else:
                self.add_row(*(Text(cell) for cell in columns))


class GitLogPath(Vertical, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.container.git_log_path, classes=Tcss.border_title_top
        )

    def compose(self) -> ComposeResult:
        yield Static(
            OperateStrings.in_dest_dir_click_path,
            id=self.ids.static.git_log_info,
        )
        yield GitLogDataTable(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = f" {self.app.dest_dir} "

    def watch_path(self) -> None:
        if self.path is None:
            return
        else:
            dest_dir_info = self.query_one(
                self.ids.static.git_log_info_q, Static
            )
            dest_dir_info.display = False
        datatable = self.query_one(
            self.ids.datatable.git_log_q, GitLogDataTable
        )
        command_result: "CommandResult" = self.app.cmd.read(
            ReadCmd.source_path, path_arg=self.path
        )
        git_log_result: "CommandResult" = self.app.cmd.read(
            ReadCmd.git_log, path_arg=Path(command_result.std_out)
        )
        datatable.populate_datatable(git_log_result)


class GitLogGlobal(Vertical, AppType):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.git_log_global)

    def compose(self) -> ComposeResult:
        yield GitLogDataTable(ids=self.ids)

    def update_global_git_log(self, command_result: "CommandResult") -> None:
        datatable = self.query_one(
            self.ids.datatable.git_log_q, GitLogDataTable
        )
        datatable.populate_datatable(command_result)
