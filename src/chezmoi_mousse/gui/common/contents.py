from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import CMD, AppType, ReadCmd, TabName, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["ContentsView"]

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

FILE_CACHE: dict[Path, ScrollableContainer] = {}


class ContentStr(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    empty_or_only_whitespace = "File is empty or contains only whitespace."
    permission_denied = "Permission denied to read file"
    read_error = "Error reading path"
    truncated = "\n--- File content truncated to"


class ContentsView(Container, AppType):

    show_path: reactive["Path | None"] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents)
        self.ids = ids
        self.current_file_container: ScrollableContainer = ScrollableContainer()

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(id=self.ids.container.dir_contents)

    def on_mount(self) -> None:
        self.dir_contents_container = self.query_one(
            self.ids.container.dir_contents_q, ScrollableContainer
        )
        if self.ids.canvas_name == TabName.add:
            self._mount_add_dir_contents(CMD.cache.dest_dir)
        else:
            self._mount_managed_dir_contents(CMD.cache.dest_dir)

    def _mount_add_dir_contents(self, dir_path: Path) -> None:
        self.current_file_container.display = False
        widgets: list[Static | Label] = []
        widgets.append(Label("Destination directory", classes=Tcss.main_section_label))
        widgets.append(
            Static("<- Click a path to see its contents.", classes=Tcss.added)
        )
        unmanaged_dirs: list[str] = sorted(
            [
                str(p.relative_to(CMD.cache.dest_dir))
                for p in list(dir_path.iterdir())
                if p not in CMD.cache.managed_dir_paths and p.is_dir()
            ]
        )
        unmanaged_files: list[str] = sorted(
            [
                str(p.relative_to(CMD.cache.dest_dir))
                for p in list(dir_path.iterdir())
                if p not in CMD.cache.managed_file_paths and p.is_file()
            ]
        )
        if unmanaged_dirs:
            widgets.append(
                Label("Contains unmanaged directories", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_dirs), classes=Tcss.info))
        if unmanaged_files:
            widgets.append(
                Label("Contains unmanaged files", classes=Tcss.sub_section_label)
            )
            widgets.append(Static("\n".join(unmanaged_files), classes=Tcss.info))
        if not unmanaged_dirs and not unmanaged_files:
            widgets.append(Static("No unmanaged paths in this directory."))
        self.dir_contents_container.remove_children()
        self.dir_contents_container.mount(*widgets)

    def _mount_managed_dir_contents(self, dir_path: Path):
        self.current_file_container.display = False
        widgets: list[Static | Label] = []
        if dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination Directory", classes=Tcss.main_section_label)
            )
        else:
            widgets.append(Label("Managed directory", classes=Tcss.main_section_label))
        widgets.append(Label(str(dir_path), classes=Tcss.sub_section_label))
        widgets.append(
            Static("<- Click a file to see its contents.", classes=Tcss.added)
        )
        self.dir_contents_container.remove_children()
        self.dir_contents_container.mount(*widgets)

    def _create_file_contents(self, file_path: Path) -> ScrollableContainer:

        def _handle_exception(
            exception: PermissionError | UnicodeDecodeError | OSError,
        ) -> Static:
            if isinstance(exception, PermissionError):
                return Static(
                    f"{ContentStr.permission_denied} for {file_path}",
                    classes=Tcss.removed,
                )
            elif isinstance(exception, UnicodeDecodeError):
                return Static(
                    f"{ContentStr.cannot_decode} for {file_path}", classes=Tcss.removed
                )
            else:
                return Static(
                    f"{ContentStr.read_error} for {file_path}", classes=Tcss.removed
                )

        def _detect_language(lines: list[str], file_path: Path) -> str | None:
            # Check shebang first
            if lines and lines[0].startswith("#!"):
                parts = lines[0].split()
                if len(parts) > 1:
                    shebang = parts[-1]
                    if shebang in SHEBANG_MAP:
                        return SHEBANG_MAP[shebang]
            # If no shebang, check path suffix
            return LANGUAGE_MAP.get(file_path.suffix.lower())

        def _read_file(file_path: Path) -> str | Static:
            try:
                truncate_size: int = 1024 * 1024  # 1Mib
                file_size = file_path.stat().st_size
                with Path.open(file_path, encoding="utf-8") as f:
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
            except (UnicodeDecodeError, PermissionError, OSError) as e:
                return _handle_exception(e)

        if file_path.exists():
            to_show = _read_file(file_path)
        else:
            cmd_result = CMD.run_cmd.read(ReadCmd.cat, path_arg=file_path)
            to_show = cmd_result.std_out
            self.app.log_cmd_result(cmd_result)
        if not to_show:
            return ScrollableContainer(Static("Nothing to show.", classes=Tcss.removed))
        if isinstance(to_show, Static):
            return ScrollableContainer(to_show)
        language = _detect_language(to_show.splitlines(), file_path)
        if language is not None:
            result = TextArea(text=to_show, language=language)
        else:
            text_obj = Text(to_show)
            ReprHighlighter().highlight(text_obj)
            result = Static(text_obj)
        return ScrollableContainer(result)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        # Hide existing views
        self.dir_contents_container.display = False
        if self.current_file_container:
            self.current_file_container.display = False

        if self.ids.canvas_name == TabName.add and show_path.is_dir():
            self._mount_add_dir_contents(show_path)
            self.dir_contents_container.display = True
        elif (
            show_path in CMD.cache.managed_dir_paths
            and show_path not in CMD.cache.status_paths
        ):
            self._mount_managed_dir_contents(show_path)
            self.dir_contents_container.display = True
        elif show_path in FILE_CACHE:
            # Ensure the first item will be the one not displayed for the longest time
            cached_container = FILE_CACHE.pop(show_path)
            FILE_CACHE[show_path] = cached_container
            cached_container.display = True
            self.current_file_container = cached_container
        else:
            # Limit cache size to 50
            if len(FILE_CACHE) >= 50:
                oldest_path = next(iter(FILE_CACHE))
                oldest_container = FILE_CACHE.pop(oldest_path)
                oldest_container.remove()

            new_container = self._create_file_contents(show_path)
            self.mount(new_container)
            FILE_CACHE[show_path] = new_container
            self.current_file_container = new_container
            self.current_file_container.display = True
