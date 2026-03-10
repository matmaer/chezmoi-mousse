from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea

from chezmoi_mousse import CMD, ReadCmd, Tcss

from .mixins import ContainerCache

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["ContentsView"]


class ContentsView(ContainerCache):

    class ContentStr(StrEnum):
        cannot_decode = "Path cannot be decoded as UTF-8:"
        empty_or_only_whitespace = "File is empty or contains only whitespace."
        permission_denied = "Permission denied to read file"
        read_error = "Error reading path"
        truncated = "\n--- File content truncated to"

    show_path: reactive["Path | None"] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents)

    def on_mount(self) -> None:
        self.show_path = CMD.cache.dest_dir

    def _create_managed_dir_container(self, dir_path: Path) -> ScrollableContainer:
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
        return ScrollableContainer(*widgets)

    def _create_file_container(self, file_path: Path) -> ScrollableContainer:
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
        return ScrollableContainer(*widgets)

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return

        container = self.container_cache.get(show_path, None)
        new_container: ScrollableContainer | None = None
        if container is None:
            # Create container based on path type
            if show_path == CMD.cache.dest_dir or (
                show_path in CMD.cache.managed_dir_paths
                and show_path not in CMD.cache.status_paths
            ):
                new_container = self._create_managed_dir_container(show_path)
            elif show_path.is_file():
                new_container = self._create_file_container(show_path)
            else:
                return
        self.update_container_display(show_path, new_container)
