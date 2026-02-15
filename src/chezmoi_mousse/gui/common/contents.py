from enum import StrEnum
from pathlib import Path

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import AppIds, AppType, CommandResult, Tcss

__all__ = ["ContentsView"]

type FileContentsDict = dict[Path, Static | TextArea]
type DirContentsDict = dict[Path, list[Static | Label]]
type ContentWidgetDict = dict[Path, Static | TextArea]


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


class ContentsView(Vertical, AppType):

    path: reactive["Path | None"] = reactive(None, init=False)
    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)

    def on_mount(self) -> None:
        self.border_title = f" {self.app.cmd_results.dest_dir} "

    def watch_path(self) -> None:
        if self.path is None:
            return
        if self.app.paths is None:
            raise ValueError("self.app.paths is None in ContentsView watch_path")
        self.remove_children()
        self.mount(self.app.paths.contents_dict[self.path])

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return
