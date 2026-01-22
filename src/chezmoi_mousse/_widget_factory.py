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

from ._app_state import AppState
from ._chezmoi_command import CommandResult, ReadCmd
from ._str_enum_names import Tcss
from ._str_enums import LogString

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
        self, dir_path: Path, has_status_paths: bool, has_x_paths: bool
    ) -> None:
        self.app = AppState.get_app()
        if self.app is None:
            raise ValueError("self.app is None")
        self.widget: Static
        self.container: ScrollableContainer
        if dir_path == self.app.dest_dir:
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
    }

    def __init__(self, diff_result: CommandResult) -> None:
        self.widgets: list[Static] = []
        self.container: ScrollableContainer
        self.std_out_lines = diff_result.std_out.splitlines()
        # Populate the container with diff widgets
        if not diff_result.std_out:
            self.container = ScrollableContainer(Static(LogString.no_stdout))
        for line in self.std_out_lines:
            classes = (
                Tcss.unhandled
            )  # visualize unhandled line start conditions for debugging
            for prefix, tcss in self.STATIC_TCSS.items():
                if line.startswith(prefix):
                    classes = tcss
                    break
            self.widgets.append(Static(line, classes=classes))
        self.container = ScrollableContainer(*self.widgets)


class GitLogTable:

    def __init__(self, git_log_result: CommandResult) -> None:
        self.data_table: DataTable[str] = DataTable()
        self.app = AppState.get_app()
        if self.app is None:
            raise ValueError("self.app is None")
        self.row_color = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        self.lines = git_log_result.std_out.splitlines()
        if len(self.lines) < 2:
            raise ValueError("Requested to construct a Git log table without data.")
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
    contents: FileContentWidgets
    diff: DiffWidgets
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


class PathDict:
    def __init__(
        self,
        dest_dir: Path,
        managed_dirs_result: CommandResult,
        managed_files_result: CommandResult,
        status_dirs_result: CommandResult,
        status_files_result: CommandResult,
    ) -> None:
        self.app = AppState.get_app()
        if self.app is None:
            raise ValueError("self.app is None")
        self.dest_dir = dest_dir
        self.managed_dir_paths = [
            Path(p) for p in managed_dirs_result.std_out.splitlines()
        ]
        self.managed_file_paths = [
            Path(p) for p in managed_files_result.std_out.splitlines()
        ]
        self.status_dir_paths = [
            Path(p[3:]) for p in status_dirs_result.std_out.splitlines()
        ]
        self.status_file_paths = [
            Path(p[3:]) for p in status_files_result.std_out.splitlines()
        ]
        self.file_path_widgets: FileWidgetDict = {}
        self.create_managed_file_node_widgets()
        self.dir_path_widgets: DirWidgetDict = {}
        self.create_managed_dir_node_widgets()
        self.dir_node_dict: DirNodeDict = {}
        self.create_dir_node_dict()

    def create_managed_file_node_widgets(self):
        if self.app is None:
            raise ValueError("self.app is None")
        for file_path in self.managed_file_paths:
            self.file_path_widgets[file_path] = FileWidgets(
                contents=FileContentWidgets(file_path=file_path),
                diff=DiffWidgets(self.app.cmd.read(ReadCmd.diff, path_arg=file_path)),
                git_log=GitLogTable(
                    self.app.cmd.read(ReadCmd.git_log, path_arg=file_path)
                ).data_table,
            )

    def has_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any status path is a descendant of the
        # provided directory.
        return any(
            path.is_relative_to(dir_path) for path in self.status_file_paths
        ) or any(path.is_relative_to(dir_path) for path in self.status_dir_paths)

    def has_x_paths_in(self, dir_path: Path) -> bool:
        # Return True if any managed path is a descendant of the
        # provided directory.
        return any(
            path.is_relative_to(dir_path) for path in self.managed_file_paths
        ) or any(path.is_relative_to(dir_path) for path in self.managed_dir_paths)

    def create_managed_dir_node_widgets(self):
        if self.app is None:
            raise ValueError("self.app is None")
        for dir_path in self.managed_dir_paths:
            has_status_paths = self.has_status_paths_in(dir_path)
            has_x_paths = self.has_x_paths_in(dir_path)
            dir_content_widgets = DirContentWidgets(
                dir_path=dir_path,
                has_status_paths=has_status_paths,
                has_x_paths=has_x_paths,
            )
            self.dir_path_widgets[dir_path] = DirWidgets(
                contents=dir_content_widgets.container,
                diff=DiffWidgets(
                    self.app.cmd.read(ReadCmd.diff, path_arg=dir_path)
                ).container,
                git_log=GitLogTable(
                    self.app.cmd.read(ReadCmd.git_log, path_arg=dir_path)
                ).data_table,
            )

    def create_dir_node_dict(self):
        for dir_path, dir_widgets in self.dir_path_widgets.items():
            status_files: FileWidgetDict = {}
            x_files: FileWidgetDict = {}
            for file_path, file_widgets in self.file_path_widgets.items():
                if file_path.parent == dir_path:  # Only direct children
                    if file_path in self.status_file_paths:
                        status_files[file_path] = file_widgets
                    elif file_path in self.managed_file_paths:
                        x_files[file_path] = file_widgets
            # Use the precomputed recursive values from PathDict methods
            self.dir_node_dict[dir_path] = DirNode(
                widgets=dir_widgets,
                status_files=status_files,
                x_files=x_files,
                has_status_paths=self.has_status_paths_in(dir_path),
                has_x_paths=self.has_x_paths_in(dir_path),
            )
