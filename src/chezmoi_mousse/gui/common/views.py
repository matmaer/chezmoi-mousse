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
    AppIds,
    AppType,
    CommandResult,
    NodeData,
    OperateString,
    ReadCmd,
    SectionLabel,
    TabName,
    Tcss,
)

if TYPE_CHECKING:
    DataTableText = DataTable[Text]
else:
    DataTableText = DataTable

__all__ = ["ContentsView", "DiffView", "GitLog"]

type DiffWidgets = list[Label | Static]


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
        super().__init__(id=self.ids.container.contents, classes=Tcss.border_title_top)

    def compose(self) -> ComposeResult:
        yield VerticalGroup(
            Label(
                SectionLabel.contents_info,
                classes=Tcss.sub_section_label,
                id=self.ids.label.contents_info,
            ),
            Static(id=self.ids.static.contents_info),
        )
        yield Label(
            SectionLabel.cat_config_output,
            classes=Tcss.sub_section_label,
            id=self.ids.label.cat_config_output,
        )
        yield Label(
            SectionLabel.file_read_output,
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
        self.file_read_label = self.query_one(self.ids.label.file_read_output_q, Label)
        self.file_read_label.display = False
        self.contents_info_static = self.query_one(
            self.ids.static.contents_info_q, Static
        )
        self.contents_info_static.update(OperateString.in_dest_dir_click_path)

    def open_file_and_update_ui(self, file_path: Path) -> None:
        try:
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.contents_info_static.update(
                    self.ContentStr.empty_or_only_whitespace
                )
                return
            with open(file_path, "rt", encoding="utf-8") as f:
                f_contents = f.read(self.truncate_size)
            if f_contents.strip() == "":
                self.contents_info_static.update(
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
            self.contents_info_static.update(
                f"{self.ContentStr.permission_denied}{file_path}"
            )
            self.rich_log.write(error.strerror)
            return
        except UnicodeDecodeError:
            self.contents_info_static.update(
                f"{self.ContentStr.cannot_decode}{file_path}"
            )
        except OSError as error:
            self.contents_info_static.update(
                f"{self.ContentStr.read_error}{file_path}: {error}"
            )
            self.rich_log.write(error.strerror)

    def write_cat_output(self, file_path: Path) -> None:
        if file_path in self.app.paths.cache.managed_files:
            self.cat_config_label.display = True
            cat_output: "CommandResult" = self.app.cmd.read(
                ReadCmd.cat, path_arg=file_path
            )
            self.contents_info_static.update(
                f"{self.ContentStr.output_from_cat}[$text-success]{cat_output.pretty_cmd}[/]"
            )
            if cat_output.std_out.strip() == "":
                self.rich_log.write(
                    Text(self.ContentStr.empty_or_only_whitespace, style="dim")
                )
            else:
                self.rich_log.write(cat_output.std_out)

    def write_dir_info(self, dir_path: Path) -> None:
        if dir_path in self.app.paths.cache.managed_dirs:
            self.contents_info_static.update(
                f"{self.ContentStr.managed_dir}[$text-accent]{dir_path}[/]"
            )
        else:
            self.contents_info_static.update(
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
        self.border_title = f" {self.node_data.path.relative_to(self.app.dest_dir)} "
        self.cat_config_label.display = False
        self.file_read_label.display = False
        self.rich_log = self.query_one(self.ids.logger.contents_q, RichLog)
        self.rich_log.clear()


class DiffStrings(StrEnum):
    # contains_status_paths = (
    #     "Directory contains the following paths with a status (recursive)"
    # )
    contains_no_status_paths = "Contains no paths with a status."
    dir_no_status = (
        "[dim]No diff available, the directory has no status and "
        "contains no paths with a status.[/]"
    )
    file_diff_lines = "File Diff Lines"
    file_no_status = "[dim]No diff available, the file has no status.[/]"
    mode_changes = "Mode Differences"
    path_lines = "Path Differences"
    truncated = "\n--- Diff output truncated to 1000 lines ---\n"


class DiffView(ScrollableContainer, AppType):

    node_data: reactive["NodeData | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.diff, classes=Tcss.border_title_top)
        if self.ids.canvas_name == TabName.re_add:
            self.diff_cmd = ReadCmd.diff_reverse
        else:
            self.diff_cmd = ReadCmd.diff

    def compose(self) -> ComposeResult:
        yield Label(SectionLabel.diff_info, classes=Tcss.sub_section_label)
        yield Static(f"{OperateString.in_dest_dir_click_path}")

    def on_mount(self) -> None:
        self.border_title = f" {self.app.dest_dir} "

    def mount_new_diff_widgets(self, diff_widgets: DiffWidgets) -> None:
        self.remove_children()
        self.mount_all(diff_widgets)

    def mount_file_no_status_widgets(self, file_path: Path) -> None:
        diff_widgets: DiffWidgets = [
            Label(f"Managed file [$text-accent]{file_path}[/]"),
            Static(f"{DiffStrings.file_no_status}"),
        ]
        self.mount_new_diff_widgets(diff_widgets)

    def mount_dir_no_status_widgets(self, dir_path: Path) -> None:
        diff_widgets: DiffWidgets = [
            Label(
                f"Managed directory [$text-accent]{dir_path}[/]",
                classes=Tcss.main_section_label,
            ),
            Static(f"{DiffStrings.dir_no_status}"),
        ]
        self.mount_new_diff_widgets(diff_widgets)

    def create_mode_diff_widgets(self, diff_lines: list[str]) -> DiffWidgets:
        diff_widgets: DiffWidgets = []
        mode_lines = [
            line
            for line in diff_lines
            if line.startswith(("old", "new", "changed", "deleted"))
        ]
        if not mode_lines:
            return []
        diff_widgets.append(
            Label(DiffStrings.mode_changes, classes=Tcss.sub_section_label)
        )
        for line in mode_lines:
            if line.startswith(("old", "deleted")):
                diff_widgets.append(Static(line, classes=Tcss.removed))
            elif line.startswith("new"):
                diff_widgets.append(Static(line, classes=Tcss.added))
                diff_lines.remove(line)
            elif line.startswith("changed"):
                diff_widgets.append(Static(line, classes=Tcss.changed))
        return diff_widgets

    def create_path_diff_widgets(self, diff_lines: list[str]) -> DiffWidgets:
        diff_widgets: DiffWidgets = []
        path_lines = [line for line in diff_lines if line.startswith(("+++", "---"))]
        if not path_lines:
            return []
        diff_widgets.append(
            Label(DiffStrings.path_lines, classes=Tcss.sub_section_label)
        )
        for line in path_lines:
            if line.startswith("---"):
                diff_widgets.append(Static(line, classes=Tcss.removed))
            elif line.startswith("+++"):
                diff_widgets.append(Static(line, classes=Tcss.added))
        return diff_widgets

    def create_file_diff_widgets(self, diff_lines: list[str]) -> DiffWidgets:
        diff_widgets: DiffWidgets = []
        file_lines = [
            line
            for line in diff_lines
            if line.startswith(("+", "-", " ")) and not line.startswith(("+++", "---"))
        ]
        # TODO: make lines limit configurable, look into paging,
        # temporary solution
        lines_limit = 1000
        lines = 0
        file_lines = [
            line
            for line in diff_lines
            if line.startswith(("+", "-", " ")) and not line.startswith(("+++", "---"))
        ]
        if not file_lines:
            return []
        diff_widgets.append(
            Label(DiffStrings.file_diff_lines, classes=Tcss.sub_section_label)
        )
        for line in file_lines:
            if line.startswith("-"):
                diff_widgets.append(Static(line, classes=Tcss.removed))
            elif line.startswith("+"):
                diff_widgets.append(Static(line, classes=Tcss.added))
            elif line.startswith(" "):
                diff_widgets.append(Static(line, classes=Tcss.context))
            lines += 1
            if lines >= lines_limit:
                diff_widgets.append(Static(DiffStrings.truncated))
                break
        return diff_widgets

    def create_status_widgets(self, node_data: "NodeData") -> DiffWidgets:
        diff_widgets: DiffWidgets = []
        diff_widgets.append(
            Label(f"Managed directory [$text-accent]{node_data.path}[/].")
        )
        return diff_widgets

    def watch_node_data(self) -> None:
        if self.node_data is None:
            return
        if self.app.dest_dir is None:
            raise ValueError("self.app.dest_dir is None in DiffView.watch_node_data")
        self.border_title = f" {self.node_data.path.relative_to(self.app.dest_dir)} "
        diff_output: "CommandResult" = self.app.cmd.read(
            self.diff_cmd, path_arg=self.node_data.path
        )
        diff_lines = diff_output.std_out.splitlines()
        diff_widgets: DiffWidgets = []
        diff_widgets.extend(self.create_mode_diff_widgets(diff_lines))
        diff_widgets.extend(self.create_path_diff_widgets(diff_lines))
        diff_widgets.extend(self.create_file_diff_widgets(diff_lines))
        if diff_widgets:
            self.mount_new_diff_widgets(diff_widgets)
            return
        if self.node_data.path in self.app.paths.cache.managed_files:
            self.mount_file_no_status_widgets(self.node_data.path)
            return
        if self.node_data.path in self.app.paths.cache.managed_dirs:
            self.mount_dir_no_status_widgets(self.node_data.path)
            return
        # Notify unhandled condition with function, class and module name
        self.notify(
            (
                f"Unhandled condition in {self.name} in "
                f"{self.__class__.__name__} in module {__name__}."
            )
        )


class GitLog(ScrollableContainer, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(id=self.ids.container.git_log, classes=Tcss.border_title_top)

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.ids.datatable.git_log)

    def on_mount(self) -> None:
        self.row_color = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        self.border_title = f" {self.app.dest_dir} "
        self.datatable: DataTable[Text] = self.query_one(
            self.ids.datatable.git_log_q, DataTable
        )

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [Text(cell_text, style=style) for cell_text in columns]
        self.datatable.add_row(*row)

    def populate_datatable(self, command_result: "CommandResult") -> None:
        if command_result.exit_code != 0 or not command_result.std_out.splitlines():
            return
        self.datatable.clear(columns=True)
        self.datatable.add_columns("COMMIT", "MESSAGE")
        for line in command_result.std_out.splitlines():
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, self.row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, self.row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, self.row_color["error"])
            else:
                self.datatable.add_row(*(Text(cell) for cell in columns))
