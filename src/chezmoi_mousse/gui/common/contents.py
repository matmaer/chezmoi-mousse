from enum import StrEnum
from pathlib import Path

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import CMD, AppIds, AppType, ReadCmd, Tcss

__all__ = ["ContentsView"]

type ContentsCache = dict[Path, ScrollableContainer]


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


class ContentsView(Container, AppType):

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)
        self.cache: ContentsCache = {}
        self.current_container: ScrollableContainer | None = None

    def on_mount(self) -> None:
        self.border_title = f" {self.app.parsed.dest_dir} "

    def create_file_contents(self, file_path: Path, managed: bool) -> Static | TextArea:
        def _detect_language(lines: list[str]) -> str | None:
            # Check shebang first
            if lines and lines[0].startswith("#!"):
                parts = lines[0].split()
                if len(parts) > 1:
                    shebang = parts[-1]
                    if shebang in SHEBANG_MAP:
                        return SHEBANG_MAP[shebang]
            # If no shebang, check path suffix
            return LANGUAGE_MAP.get(file_path.suffix.lower())

        def _read_file(file_path: Path) -> str:
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

        if managed is False:
            to_show = _read_file(file_path)
        else:
            to_show = CMD.read(ReadCmd.cat, path_arg=file_path).std_out
        if not to_show:
            return Static("Nothing to show.")
        language = _detect_language(to_show.splitlines())
        if language is not None:
            result = TextArea(text=to_show, language=language)
        else:
            text_obj = Text(to_show)
            ReprHighlighter().highlight(text_obj)
            result = Static(text_obj)
        return result

    def create_dir_contents(
        self, dir_path: Path, dest_dir: Path
    ) -> ScrollableContainer:
        widgets: list[Static | Label] = [Label(f"Directory: {dir_path}")]

        if dir_path == dest_dir:
            widgets.append(Static("in dest dir"))
        else:
            widgets.append(
                Static(f"the directory {dir_path} has no managed or status paths")
            )
        return ScrollableContainer(*widgets)

    def _cache_container(
        self, path: Path, *widgets: Static | TextArea | Label
    ) -> ScrollableContainer:
        """Helper to mount and cache a ScrollableContainer with widgets."""
        container = ScrollableContainer()
        self.mount(container)
        if widgets:
            container.mount_all(widgets)
        self.cache[path] = container
        return container

    def watch_show_path(self) -> None:
        if self.show_path is None:
            return

        if self.show_path not in self.cache:
            # Managed files (ApplyTab/ReAddTab)
            if self.show_path in self.app.parsed.managed_files:
                widget = self.create_file_contents(
                    file_path=self.show_path, managed=True
                )
                self._cache_container(self.show_path, widget)

            # Managed directories (ApplyTab/ReAddTab)
            elif self.show_path in self.app.parsed.managed_dirs:
                container = self.create_dir_contents(
                    dir_path=self.show_path, dest_dir=self.app.parsed.dest_dir
                )
                self.mount(container)
                self.cache[self.show_path] = container

            # Unmanaged files (AddTab)
            elif self.show_path.is_file():
                widget = self.create_file_contents(
                    file_path=self.show_path, managed=False
                )
                self._cache_container(self.show_path, widget)

            # Unmanaged directories (AddTab)
            elif self.show_path.is_dir():
                widget = Static(f"{self.show_path} is a directory not managed.")
                self._cache_container(self.show_path, widget)

            else:
                return

        # Hide current container, show the selected one
        if self.current_container is not None:
            self.current_container.display = False
        self.cache[self.show_path].display = True
        self.current_container = self.cache[self.show_path]
