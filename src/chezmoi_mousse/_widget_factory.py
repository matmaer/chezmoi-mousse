"""These classes accept a CommandResult or Path object for the CatFileWidgets class.

These are factories in the sense they don't contain anything but an init method to
construct a collection of textual widgets which can be cached and used to set the
content for ContentSwitchers when clicking paths in the Tree and DirectoryTree widgets.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import ScrollableContainer
from textual.widgets import DataTable, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from ._chezmoi_command import ChezmoiCommand, CommandResult, ReadCmd
from ._str_enum_names import TabName, Tcss
from ._str_enums import LogString, StatusCode

__all__ = ["DirNodeDict", "PathDict"]


class ContentStr(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    empty_or_only_whitespace = "File is empty or contains only whitespace."
    managed_dir = "Managed directory"
    output_from_cat = (
        "File does not exist on disk, output from chezmoi cat on source path."
    )
    permission_denied = "Permission denied to read file"
    read_error = "Error reading path"
    truncated = "\n--- File content truncated to"
    unmanaged_dir = "Unmanaged directory"


class FileContentWidgets:
    """Creates a .container attribute containing a ScrollableContainer with a TextArea
    for recognized languages or a single Static widget with highlighting for others."""

    BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}
    # Additional mappings for "similar" language files to show in TextArea
    LANGUAGE_MAP = BUILTIN_MAP | {
        ".cfg": BUILTIN_MAP["toml"],
        ".ini": BUILTIN_MAP["toml"],
        ".sh": BUILTIN_MAP["bash"],
        ".yml": BUILTIN_MAP["yaml"],
        ".zsh": BUILTIN_MAP["bash"],
    }
    # Separate mapping for common shebang interpreters to languages
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

    def __init__(
        self, cat_result: CommandResult | None = None, file_path: Path | None = None
    ) -> None:
        self.widget: Static | TextArea
        self.container: ScrollableContainer
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
        self.container = ScrollableContainer(self.widget)

    def _detect_language(self, lines: list[str]) -> str | None:
        if self.path_arg is None:
            return None
        # Check shebang first
        if lines and lines[0].startswith("#!"):
            parts = lines[0].split()
            if len(parts) > 1:
                shebang = parts[-1]
                if shebang in self.SHEBANG_MAP:
                    return self.SHEBANG_MAP[shebang]
        # If no shebang, check path suffix
        return self.LANGUAGE_MAP.get(self.path_arg.suffix.lower())

    def _read_file(self, file_path: Path) -> str:
        try:
            truncate_size: int = 100 * 1024  # 100 KiB
            file_size = file_path.stat().st_size
            with open(file_path, "rt", encoding="utf-8") as f:
                f_contents = f.read(truncate_size)
            if f_contents.strip() == "":
                return ContentStr.empty_or_only_whitespace
            if file_size > truncate_size:
                return (
                    f_contents
                    + f"\n--- {ContentStr.truncated} {truncate_size / 1024} KiB ---"
                )
            return "Nothing to read." if f_contents == "" else f_contents
        except PermissionError:
            return f"{ContentStr.permission_denied} for {file_path}"
        except UnicodeDecodeError:
            return f"{ContentStr.cannot_decode} for {file_path}"
        except OSError:
            return f"{ContentStr.read_error}"


class DirContentWidgets:
    """Produces a ScrollableContainer containing Labels and Static widgets to illustrate
    the directory contents."""

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


class DiffWidgets:
    """Creates a .container attribute containing a ScrollableContainer with Static
    widgets for each diff line in the CommandResult output.

    If no diff is available, aka stdout is empty, it will contain one Static informing
    that there is no diff available.
    """

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

    def __init__(self, diff_result: CommandResult) -> None:
        self.widgets: list[Static] = []
        self.container: ScrollableContainer
        self.std_out_lines = diff_result.std_out.splitlines()
        # Populate the container with diff widgets
        if not diff_result.std_out:
            self.container = ScrollableContainer(Static(LogString.no_stdout))
        classes = self.STATIC_TCSS["unhandled"]
        for line in self.std_out_lines:
            for prefix, tcss in self.STATIC_TCSS.items():
                if line.startswith(prefix):
                    classes = tcss
                    break
            self.widgets.append(Static(line, classes=classes.value))
        self.container = ScrollableContainer(*self.widgets)


class GitLogTable:

    def __init__(
        self, git_log_result: CommandResult, theme_variables: dict[str, str]
    ) -> None:
        self.row_color = {
            "ok": theme_variables["text-success"],
            "warning": theme_variables["text-warning"],
            "error": theme_variables["text-error"],
        }
        self.lines = git_log_result.std_out.splitlines()
        if len(self.lines) == 0:
            raise ValueError("Requested to construct a Git log table without data.")
        self.data_table: DataTable[str] = DataTable[str]()
        self._populate_datatable()

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: list[str] = [f"[{style}]{cell_text}[/{style}]" for cell_text in columns]
        self.data_table.add_row(*row)

    def _populate_datatable(self) -> None:
        self.data_table.add_columns("COMMIT", "MESSAGE")
        for line in self.lines:
            columns = line.split(";", maxsplit=1)
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, self.row_color["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, self.row_color["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, self.row_color["error"])
            else:
                self.data_table.add_row(*columns)


@dataclass(slots=True)
class FileWidgets:
    label: str
    contents: FileContentWidgets
    diff: ScrollableContainer
    git_log: DataTable[str]


type FileWidgetDict = dict[Path, FileWidgets]


@dataclass(slots=True)
class DirWidgets:
    contents: ScrollableContainer
    diff: ScrollableContainer
    git_log: DataTable[str]


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
        cmd: ChezmoiCommand,
        dest_dir: Path,
        theme_variables: dict[str, str],
        managed_dirs_result: CommandResult,
        managed_files_result: CommandResult,
        status_dirs_result: CommandResult,
        status_files_result: CommandResult,
    ) -> None:
        self.dest_dir = dest_dir
        self.cmd = cmd
        self.theme_variables = theme_variables
        self.node_colors: dict[str, str] = {
            StatusCode.Added: self.theme_variables["text-success"],
            StatusCode.Deleted: self.theme_variables["text-error"],
            StatusCode.Modified: self.theme_variables["text-warning"],
            StatusCode.No_Change: self.theme_variables["warning-darken-2"],
            StatusCode.Run: self.theme_variables["error"],
            StatusCode.X: self.theme_variables["text-secondary"],
        }
        self.managed_dirs: list[Path] = []
        self.managed_files: list[Path] = []
        self.status_dirs: list[Path] = []
        self.status_files: list[Path] = []
        self.x_dirs: list[Path] = []
        self.x_files: list[Path] = []
        self.apply_dir_status: StatusPath = {}
        self.apply_file_status: StatusPath = {}
        self.re_add_dir_status: StatusPath = {}
        self.re_add_file_status: StatusPath = {}
        self._update_managed_and_status_paths(
            managed_dirs_result,
            managed_files_result,
            status_dirs_result,
            status_files_result,
        )

        self.status_dir_lines = status_dirs_result.std_out.splitlines()
        self.status_file_lines = status_files_result.std_out.splitlines()
        self.apply_file_widgets: FileWidgetDict = {}
        self.re_add_file_widgets: FileWidgetDict = {}
        self.create_managed_file_node_widgets()
        self.apply_dir_widgets: DirWidgetDict = {}
        self.re_add_dir_widgets: DirWidgetDict = {}
        self.create_managed_dir_node_widgets()
        self.apply_dir_node_dict: DirNodeDict = {}
        self.re_add_dir_node_dict: DirNodeDict = {}

        self.dir_node_dict: DirNodeDict = {}
        self.create_dir_node_dict()

    def _update_managed_and_status_paths(
        self,
        managed_dirs_result: CommandResult,
        managed_files_result: CommandResult,
        status_dirs_result: CommandResult,
        status_files_result: CommandResult,
    ) -> None:
        for line in status_dirs_result.std_out.splitlines():
            parsed_path = Path(line[3:])
            self.status_dirs.append(parsed_path)
            self.apply_dir_status[parsed_path] = StatusCode(line[0])
            self.re_add_dir_status[parsed_path] = StatusCode(line[1])
        for line in status_files_result.std_out.splitlines():
            parsed_path = Path(line[3:])
            self.status_files.append(parsed_path)
            self.apply_file_status[parsed_path] = StatusCode(line[0])
            self.re_add_file_status[parsed_path] = StatusCode(line[1])
        for line in managed_dirs_result.std_out.splitlines():
            parsed_path = Path(line)
            self.managed_dirs.append(parsed_path)
            if parsed_path not in self.status_dirs:
                self.x_dirs.append(parsed_path)
        for line in managed_files_result.std_out.splitlines():
            parsed_path = Path(line)
            self.managed_files.append(parsed_path)
            if parsed_path not in self.status_files:
                self.x_files.append(parsed_path)

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

    def create_managed_file_node_widgets(self):
        for file_path in self.managed_files:
            git_log_table = GitLogTable(
                self.cmd.read(ReadCmd.git_log, path_arg=file_path), self.theme_variables
            ).data_table
            contents = FileContentWidgets(file_path=file_path)
            self.apply_file_widgets[file_path] = FileWidgets(
                contents=contents,
                diff=DiffWidgets(
                    self.cmd.read(ReadCmd.diff, path_arg=file_path)
                ).container,
                git_log=git_log_table,
                label=self.create_label(file_path, TabName.apply),
            )
            self.re_add_file_widgets[file_path] = FileWidgets(
                contents=contents,
                diff=DiffWidgets(
                    self.cmd.read(ReadCmd.diff_reverse, path_arg=file_path)
                ).container,
                git_log=git_log_table,
                label=self.create_label(file_path, TabName.re_add),
            )

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

    def create_managed_dir_node_widgets(self):
        for dir_path in self.managed_dirs:
            has_status_paths = self.has_status_paths_in(dir_path)
            has_x_paths = self.has_x_paths_in(dir_path)
            dir_content_widgets = DirContentWidgets(
                dir_path=dir_path,
                has_status_paths=has_status_paths,
                has_x_paths=has_x_paths,
                dest_dir=self.dest_dir,
            )
            git_log_table = GitLogTable(
                self.cmd.read(ReadCmd.git_log, path_arg=dir_path), self.theme_variables
            ).data_table
            self.apply_dir_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container,
                diff=DiffWidgets(
                    self.cmd.read(ReadCmd.diff, path_arg=dir_path)
                ).container,
                git_log=git_log_table,
            )
            self.re_add_dir_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container,
                diff=DiffWidgets(
                    self.cmd.read(ReadCmd.diff_reverse, path_arg=dir_path)
                ).container,
                git_log=git_log_table,
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

    def update_cache(self):
        self._update_managed_and_status_paths(
            self.cmd.read(ReadCmd.managed_dirs),
            self.cmd.read(ReadCmd.managed_files),
            self.cmd.read(ReadCmd.status_dirs),
            self.cmd.read(ReadCmd.status_files),
        )
