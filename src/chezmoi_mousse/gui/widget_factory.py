from dataclasses import dataclass, field
from enum import StrEnum
from itertools import groupby
from pathlib import Path

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import ScrollableContainer
from textual.widgets import DataTable, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import (
    ChezmoiCommand,
    CommandResult,
    LogString,
    ReadCmd,
    StatusCode,
    TabName,
    Tcss,
)

__all__ = ["PathDict"]


BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}
# Additional mappings for "similar" language files to choose TextArea
LANGUAGE_MAP = BUILTIN_MAP | {
    ".cfg": BUILTIN_MAP["toml"],
    ".ini": BUILTIN_MAP["toml"],
    ".sh": BUILTIN_MAP["bash"],
    ".yml": BUILTIN_MAP["yaml"],
    ".zsh": BUILTIN_MAP["bash"],
}
SHEBANG_MAP = {
    "python": "python",
    "python3": "python",
    "bash": "bash",
    "sh": "bash",
    "zsh": "bash",
    "node": "javascript",
    "java": "java",
    "go": "go",
    "rustc": "rust",
}
STATIC_TCSS = {
    " ": Tcss.context,
    "+": Tcss.added,
    "-": Tcss.removed,
    "new": Tcss.added,
    "old": Tcss.removed,
    "index": Tcss.context,
    "changed": Tcss.changed,
    "deleted": Tcss.removed,
    "unhandled": Tcss.unhandled,
}


class ContentStr(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    empty_or_only_whitespace = "File is empty or contains only whitespace."
    permission_denied = "Permission denied to read file"
    read_error = "Error reading path"
    truncated = "\n--- File content truncated to"


class FileContents:
    """Creates a .widget attribute containing a TextArea for recognized languages or a
    single Static widget with highlighting for others."""

    def __init__(
        self, cat_result: CommandResult | None = None, file_path: Path | None = None
    ) -> None:
        self.widget: Static | TextArea = Static("Nothing to show.")
        if file_path is not None:
            self.path_arg = file_path
            self.to_show = self._read_file(file_path)
        elif cat_result is not None:
            self.path_arg = cat_result.path_arg
            self.to_show = cat_result.std_out
        else:
            raise ValueError("cat_result and file_path cannot both be None")
        if not self.to_show:
            self.widget = Static("Nothing to show.")
            return
        self.language = self._detect_language(self.to_show.splitlines())
        if self.language is not None:
            self.widget = TextArea(text=self.to_show, language=self.language)
        else:
            text_obj = Text(self.to_show)
            ReprHighlighter().highlight(text_obj)
            self.widget = Static(text_obj)

    def _detect_language(self, lines: list[str]) -> str | None:
        if self.path_arg is None:
            return None
        # Check shebang first
        if lines and lines[0].startswith("#!"):
            parts = lines[0].split()
            if len(parts) > 1:
                shebang = parts[-1]
                if shebang in SHEBANG_MAP:
                    return SHEBANG_MAP[shebang]
        # If no shebang, check path suffix
        return LANGUAGE_MAP.get(self.path_arg.suffix.lower())

    def _read_file(self, file_path: Path) -> str:

        try:
            truncate_size: int = 100 * 1024  # 100 KiB
            file_size = file_path.stat().st_size
            with open(file_path, "rt", encoding="utf-8") as f:
                f_contents = f.read(truncate_size)
            if f_contents.strip() == "":
                return ContentStr.empty_or_only_whitespace
            elif file_size > truncate_size:
                return (
                    f_contents
                    + f"\n--- {ContentStr.truncated} {truncate_size / 1024} KiB ---"
                )
            else:
                return "Nothing to read." if f_contents == "" else f_contents
        except PermissionError:
            return f"{ContentStr.permission_denied} for {file_path}"
        except UnicodeDecodeError:
            return f"{ContentStr.cannot_decode} for {file_path}"
        except OSError:
            return f"{ContentStr.read_error}"


class DirContents:

    def __init__(
        self, dir_path: Path, has_status_paths: bool, has_x_paths: bool, dest_dir: Path
    ) -> None:
        self.widget: Static
        self.container: ScrollableContainer
        if dir_path == dest_dir:
            self.widget = Static("in dest dir")
        elif has_status_paths and has_x_paths:
            self.widget = Static(
                f"a directory {dir_path} with status and managed paths"
            )
        elif has_status_paths:
            self.widget = Static(f"a directory {dir_path} with status paths")
        elif has_x_paths:
            self.widget = Static(f"a directory {dir_path} with managed paths")
        else:
            self.widget = Static(
                f"the directory {dir_path} has no managed or status paths"
            )
        self.container = ScrollableContainer(self.widget)


type ContentWidgetDict = dict[Path, Static | TextArea]

type ContentsDict = dict[Path, Static | TextArea]


class DiffWidgets:
    """Creates a list of Static in the .widgets attribute widgets for each diff line in
    the CommandResult output.

    If no diff is available, aka stdout is empty, it will contain one Static informing
    that there is no diff available.
    """

    def __init__(self, diff_result: CommandResult) -> None:
        self.widgets: list[Static] = []
        if not diff_result.std_out:
            self.widgets = [Static(LogString.no_stdout)]
            return

        lines = diff_result.std_out.splitlines()

        def get_prefix(line: str) -> str:
            for p in STATIC_TCSS:
                if line.startswith(p):
                    return p
            return "unhandled"

        for prefix, group_lines in groupby(lines, key=get_prefix):
            group_list = list(group_lines)
            if prefix in ("+", "-"):
                text = "\n".join(group_list)
                self.widgets.append(Static(text, classes=STATIC_TCSS[prefix].value))
            else:
                for line in group_list:
                    self.widgets.append(Static(line, classes=STATIC_TCSS[prefix].value))


type DiffWidgetDict = dict[Path, list[Static]]


class GitLogTable(DataTable[str]):

    def __init__(
        self, git_log_result: CommandResult, theme_variables: dict[str, str]
    ) -> None:
        super().__init__()
        self.git_log_result = git_log_result
        self.row_color = {
            "ok": theme_variables["text-success"],
            "warning": theme_variables["text-warning"],
            "error": theme_variables["text-error"],
        }

    def on_mount(self) -> None:
        self._populate_datatable()

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: list[str] = [f"[{style}]{cell_text}[/{style}]" for cell_text in columns]
        self.add_row(*row)

    def _populate_datatable(self) -> None:
        self.add_columns("COMMIT", "MESSAGE")
        lines = self.git_log_result.std_out.splitlines()
        if len(lines) == 0:
            self.add_row("No commits;No git log available for this path.")
            return
        for line in lines:
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, self.row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, self.row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, self.row_color["error"])
            else:
                self.add_row(*columns)


type GitLogTableDict = dict[Path, DataTable[str]]


@dataclass(slots=True)
class FileWidgets:
    label: str


type FileWidgetDict = dict[Path, FileWidgets]


@dataclass(slots=True)
class DirWidgets:
    contents: ScrollableContainer


type DirWidgetDict = dict[Path, DirWidgets]


@dataclass(slots=True)
class DirNode:
    label: str
    widgets: DirWidgets
    status_files: FileWidgetDict = field(
        default_factory=dict[Path, FileWidgets]
    )  # Files with a status other than X
    x_files: FileWidgetDict = field(
        default_factory=dict[Path, FileWidgets]
    )  # Files with status X
    # True if the dir has status_files or if any subdir or file has a status other than
    # X, no matter how deeply nested
    has_status_paths: bool = False
    # True if the dir has x_files or if any subdir or file has a status with status X,
    # no matter how deeply nested
    has_x_paths: bool = False


type DirNodeDict = dict[Path, DirNode]


type StatusPath = dict[Path, StatusCode]


class PathDict:
    def __init__(
        self,
        dest_dir: Path,
        theme_variables: dict[str, str],
        managed_dirs: list[Path],
        managed_files: list[Path],
        apply_dir_status: dict[Path, StatusCode],
        apply_file_status: dict[Path, StatusCode],
        re_add_dir_status: dict[Path, StatusCode],
        re_add_file_status: dict[Path, StatusCode],
    ) -> None:
        self.dest_dir = dest_dir
        self.cmd = ChezmoiCommand()
        self.theme_variables = theme_variables
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.theme_variables["text-success"],
            StatusCode.Deleted: self.theme_variables["text-error"],
            StatusCode.Modified: self.theme_variables["text-warning"],
            StatusCode.No_Change: self.theme_variables["warning-darken-2"],
            StatusCode.Run: self.theme_variables["error"],
            StatusCode.X: self.theme_variables["text-secondary"],
        }
        self.managed_dirs: list[Path] = [self.dest_dir] + managed_dirs
        self.managed_files: list[Path] = managed_files
        self.status_dirs: list[Path] = list(apply_dir_status.keys())
        self.status_files: list[Path] = list(apply_file_status.keys())
        self.x_dirs: list[Path] = []
        self.x_files: list[Path] = []
        self.apply_dir_status: StatusPath = apply_dir_status
        self.apply_file_status: StatusPath = apply_file_status
        self.re_add_dir_status: StatusPath = re_add_dir_status
        self.re_add_file_status: StatusPath = re_add_file_status
        # Compute x_dirs and x_files
        for path in self.managed_dirs:
            if path not in self.status_dirs:
                self.x_dirs.append(path)
        for path in self.managed_files:
            if path not in self.status_files:
                self.x_files.append(path)
        self.contents_dict: ContentWidgetDict = {}
        self._update_contents_dict()
        self.git_log_tables: GitLogTableDict = {}
        self._update_git_log_tables()
        self.apply_diff_widgets: DiffWidgetDict = {}
        self.re_add_diff_widgets: DiffWidgetDict = {}
        self._update_diff_widgets()
        self.content_widgets: ContentWidgetDict = {}
        self._update_content_widgets()
        self.apply_file_widgets: FileWidgetDict = {}
        self.re_add_file_widgets: FileWidgetDict = {}
        self.create_managed_file_node_widgets()
        self.apply_dir_widgets: DirWidgetDict = {}
        self.re_add_dir_widgets: DirWidgetDict = {}
        self.create_managed_dir_node_widgets()
        self.apply_dir_node_dict: DirNodeDict = {}
        self.re_add_dir_node_dict: DirNodeDict = {}
        self.create_dir_node_dict()

    def _update_contents_dict(self):
        for path in self.managed_files:
            self.contents_dict[path] = FileContents(file_path=path).widget
        for path in self.managed_dirs:
            has_status_paths = self.has_status_paths_in(path)
            has_x_paths = self.has_x_paths_in(path)
            self.contents_dict[path] = DirContents(
                dir_path=path,
                has_status_paths=has_status_paths,
                has_x_paths=has_x_paths,
                dest_dir=self.dest_dir,
            ).widget

    def _update_git_log_tables(self):
        all_paths = self.managed_dirs + self.managed_files
        self.git_log_tables[self.dest_dir] = GitLogTable(
            self.cmd.read(ReadCmd.git_log), self.theme_variables
        )
        for path in all_paths:
            if path == self.dest_dir:
                continue
            self.git_log_tables[path] = GitLogTable(
                self.cmd.read(ReadCmd.git_log, path_arg=path), self.theme_variables
            )

    def _update_diff_widgets(self):
        all_paths = self.managed_dirs + self.managed_files
        for path in all_paths:
            self.apply_diff_widgets[path] = DiffWidgets(
                self.cmd.read(ReadCmd.diff, path_arg=path)
            ).widgets
            self.re_add_diff_widgets[path] = DiffWidgets(
                self.cmd.read(ReadCmd.diff_reverse, path_arg=path)
            ).widgets

    def _update_content_widgets(self):
        for path in self.managed_files:
            self.content_widgets[path] = FileContents(file_path=path).widget
        for path in self.managed_dirs:
            self.content_widgets[path] = DirContents(
                dest_dir=self.dest_dir,
                has_status_paths=self.has_status_paths_in(path),
                has_x_paths=self.has_x_paths_in(path),
                dir_path=path,
            ).widget

    def create_label(self, path: Path, tab_name: TabName) -> str:
        italic = " italic" if not path.exists() else ""
        apply_color = self.node_colors.get(
            self.apply_file_status.get(path, StatusCode.X)
        )
        if tab_name == TabName.apply:
            apply_color = self.node_colors.get(
                self.apply_file_status.get(path, StatusCode.X)
            )
            return f"[{apply_color}" f"{italic}]{path.name}[/]"
        elif tab_name == TabName.re_add:
            re_add_color = self.node_colors.get(
                self.re_add_file_status.get(path, StatusCode.X)
            )
            return f"[{re_add_color}" f"{italic}]{path.name}[/]"
        else:
            raise ValueError(f"Unhandled tab name: {tab_name}")

    def has_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any path with a status other than X, is a descendant of the
        # provided directory.
        return any(path.is_relative_to(dir_path) for path in self.status_files) or any(
            path.is_relative_to(dir_path) for path in self.status_dirs
        )

    def has_x_paths_in(self, dir_path: Path) -> bool:
        # Return True if any managed path is a descendant of the
        # provided directory containing paths with status X.
        return any(path.is_relative_to(dir_path) for path in self.x_files) or any(
            path.is_relative_to(dir_path) for path in self.x_dirs
        )

    def create_managed_file_node_widgets(self):
        for file_path in self.managed_files:
            self.apply_file_widgets[file_path] = FileWidgets(
                label=self.create_label(file_path, TabName.apply)
            )
            self.re_add_file_widgets[file_path] = FileWidgets(
                label=self.create_label(file_path, TabName.re_add)
            )

    def create_managed_dir_node_widgets(self):
        for dir_path in self.managed_dirs:
            has_status_paths = self.has_status_paths_in(dir_path)
            has_x_paths = self.has_x_paths_in(dir_path)
            dir_content_widgets = DirContents(
                dir_path=dir_path,
                has_status_paths=has_status_paths,
                has_x_paths=has_x_paths,
                dest_dir=self.dest_dir,
            )
            self.apply_dir_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container
            )
            self.re_add_dir_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container
            )

    def create_dir_node_dict(self):
        for dir_path, dir_widgets in self.apply_dir_widgets.items():
            status_files: FileWidgetDict = {}
            x_files: FileWidgetDict = {}
            for file_path, file_widgets in self.apply_file_widgets.items():
                if file_path.parent == dir_path:  # Only direct children
                    if file_path in self.status_files:
                        status_files[file_path] = file_widgets
                    elif file_path in self.managed_files:
                        x_files[file_path] = file_widgets
            self.apply_dir_node_dict[dir_path] = DirNode(
                label=self.create_label(dir_path, TabName.apply),
                widgets=dir_widgets,
                status_files=status_files,
                x_files=x_files,
                has_status_paths=self.has_status_paths_in(dir_path),
                has_x_paths=self.has_x_paths_in(dir_path),
            )
        for dir_path, dir_widgets in self.re_add_dir_widgets.items():
            status_files: FileWidgetDict = {}
            x_files: FileWidgetDict = {}
            for file_path, file_widgets in self.re_add_file_widgets.items():
                if file_path.parent == dir_path:  # Only direct children
                    if file_path in self.status_files:
                        status_files[file_path] = file_widgets
                    elif file_path in self.managed_files:
                        x_files[file_path] = file_widgets
            self.re_add_dir_node_dict[dir_path] = DirNode(
                label=self.create_label(dir_path, TabName.re_add),
                widgets=dir_widgets,
                status_files=status_files,
                x_files=x_files,
                has_status_paths=self.has_status_paths_in(dir_path),
                has_x_paths=self.has_x_paths_in(dir_path),
            )
