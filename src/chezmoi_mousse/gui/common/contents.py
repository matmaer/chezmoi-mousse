from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import CMD, AppType, ReadCmd, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["ContentsView"]

BUILTIN_MAP = {lang: lang for lang in BUILTIN_LANGUAGES}
# Additional mappings for "similar" language files to choose TextArea


class ContentsView(Container, AppType):

    class ContentStr(StrEnum):
        cannot_decode = "Path cannot be decoded as UTF-8:"
        empty_or_only_whitespace = "File is empty or contains only whitespace."
        permission_denied = "Permission denied to read file"
        read_error = "Error reading path"
        truncated = "\n--- File content truncated to"

    show_path: reactive["Path | None"] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents)
        self.ids = ids
        self.container_cache: dict[Path, ScrollableContainer] = {}
        self.current_container_path: Path | None = None
        self.language_map = BUILTIN_MAP | {
            ".cfg": BUILTIN_MAP["toml"],
            ".ini": BUILTIN_MAP["toml"],
            ".sh": BUILTIN_MAP["bash"],
            ".yml": BUILTIN_MAP["yaml"],
            ".zsh": BUILTIN_MAP["bash"],
        }
        self.shebang_map = {
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

    def on_mount(self) -> None:
        self.show_path = CMD.cache.dest_dir

    def _cache_managed_dir_contents(self, dir_path: Path) -> None:
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
        self.container_cache[dir_path] = ScrollableContainer(*widgets)
        self.current_container_path = dir_path

    def _cache_file_contents(self, file_path: Path) -> None:
        widgets: list[Label | Static | TextArea] = []

        def _detect_language(lines: list[str], file_path: Path) -> str | None:
            # Check shebang first
            if lines and lines[0].startswith("#!"):
                parts = lines[0].split()
                if len(parts) > 1:
                    shebang = parts[-1]
                    if shebang in self.shebang_map:
                        return self.shebang_map[shebang]
            # If no shebang, check path suffix
            return self.language_map.get(file_path.suffix.lower())

        def _handle_exception(
            exception: PermissionError | UnicodeDecodeError | OSError,
        ) -> str:
            if isinstance(exception, PermissionError):
                return f"{ContentsView.ContentStr.permission_denied} for {file_path}"
            elif isinstance(exception, UnicodeDecodeError):
                return f"{ContentsView.ContentStr.cannot_decode} for {file_path}"
            else:
                return f"{ContentsView.ContentStr.read_error} for {file_path}"

        def _read_file(file_path: Path) -> str:
            file_contents: str = ""
            if not file_path.exists():
                cmd_result = CMD.run_cmd.read(ReadCmd.cat, path_arg=file_path)
                file_contents = cmd_result.std_out
                self.app.log_cmd_result(cmd_result)
            try:
                truncate_size: int = 1024 * 1024  # 1Mib
                file_size = file_path.stat().st_size
                with Path.open(file_path, encoding="utf-8") as f:
                    f_contents = f.read(truncate_size)
                if f_contents.strip() == "":
                    file_contents = ContentsView.ContentStr.empty_or_only_whitespace
                elif file_size > truncate_size:
                    file_contents = (
                        f_contents + f"\n--- {ContentsView.ContentStr.truncated} "
                        f"{truncate_size / 1024} KiB ---"
                    )
                else:
                    file_contents = (
                        "Nothing to read." if f_contents == "" else f_contents
                    )

            except (UnicodeDecodeError, PermissionError, OSError) as e:
                file_contents = _handle_exception(e)
            return file_contents

        file_contents = _read_file(file_path)
        language = _detect_language(file_contents.splitlines(), file_path)
        if language is not None:
            widgets.append(TextArea(text=file_contents, language=language))
        else:
            text_obj = Text(file_contents)
            ReprHighlighter().highlight(text_obj)
            widgets.append(Static(text_obj))
        self.container_cache[file_path] = ScrollableContainer(*widgets)

    def purge_mounted_containers(self, changed_paths: list["Path"]) -> None:
        keys_to_remove = [
            cached_path
            for cached_path in self.container_cache
            if any(
                cached_path == changed_path or changed_path in cached_path.parents
                for changed_path in changed_paths
            )
        ]

        for cached_path in keys_to_remove:
            container = self.container_cache.pop(cached_path, None)
            if container is not None:
                container.remove()

        if self.current_container_path in keys_to_remove:
            self.current_container_path = None

        self.show_path = CMD.cache.dest_dir

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return

        # Hide the previously displayed container
        if self.current_container_path is not None:
            previous_container = self.container_cache.get(
                self.current_container_path, None
            )
            if previous_container is not None:
                previous_container.display = False

        is_mounted = show_path in self.container_cache
        if is_mounted:
            self.container_cache[show_path].display = True
            self.current_container_path = show_path
            return

        if show_path == CMD.cache.dest_dir or (
            show_path in CMD.cache.managed_dir_paths
            and show_path not in CMD.cache.status_paths
        ):
            self._cache_managed_dir_contents(show_path)
            self.mount(self.container_cache[show_path])
            self.current_container_path = show_path
        elif show_path.is_file():
            self._cache_file_contents(show_path)
            self.mount(self.container_cache[show_path])
            self.current_container_path = show_path
