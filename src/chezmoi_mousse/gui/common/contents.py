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
    from chezmoi_mousse import AppIds, DirNode

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


class ContentStr(StrEnum):
    cannot_decode = "Path cannot be decoded as UTF-8:"
    empty_or_only_whitespace = "File is empty or contains only whitespace."
    permission_denied = "Permission denied to read file"
    read_error = "Error reading path"
    truncated = "\n--- File content truncated to"


class ContentsView(Container, AppType):

    show_path: reactive["Path"] = reactive(CMD.dest_dir, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)
        self.ids = ids
        self.file_cache: dict[Path, ScrollableContainer] = {}
        self.current_file_container: ScrollableContainer = ScrollableContainer()

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(id=self.ids.container.file_contents)
        yield ScrollableContainer(id=self.ids.container.dir_contents)

    def on_mount(self) -> None:
        self.dir_contents_container = self.query_one(
            self.ids.container.dir_contents_q, ScrollableContainer
        )
        self.file_contents_container = self.query_one(
            self.ids.container.file_contents_q, ScrollableContainer
        )
        self.file_contents_container.display = False
        self.border_title = f" {CMD.dest_dir} "
        if self.ids.canvas_name == TabName.add:
            self.dir_contents_container.mount(
                *self._create_add_dir_contents(CMD.dest_dir)
            )
        else:
            self.dir_contents_container.mount(*self.dir_nodes[CMD.dest_dir].dir_widgets)

    @property
    def dir_nodes(self) -> dict[Path, "DirNode"]:
        if self.ids.canvas_name == TabName.apply:
            return CMD.apply_dir_nodes
        else:
            return CMD.re_add_dir_nodes

    def _set_border_title(self) -> None:
        if self.show_path == CMD.dest_dir:
            self.border_title = f" {CMD.dest_dir} "
        else:
            self.border_title = f" {self.show_path.name} "

    def _create_add_dir_contents(self, show_dir_path: Path) -> list[Static | Label]:
        widgets: list[Static | Label] = []
        if show_dir_path == CMD.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            widgets.append(
                Static("<- Click a path to see its contents.", classes=Tcss.added)
            )
            return widgets
        unmanaged: list[str] = [
            str(p)
            for p in list(show_dir_path.iterdir())
            if p not in CMD.managed_dirs and p not in CMD.managed_files
        ]
        if not unmanaged:
            widgets.append(Static("No unmanaged paths in this directory."))
            return widgets
        widgets.append(
            Label("Contains unmanaged paths", classes=Tcss.sub_section_label)
        )
        widgets.append(Static("\n".join(unmanaged)))
        return widgets

    def _create_file_contents(
        self, file_path: Path, managed: bool
    ) -> Static | TextArea:
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
                with open(file_path, encoding="utf-8") as f:
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
            try:
                to_show = CMD.run_cmd.read(ReadCmd.cat, path_arg=file_path).std_out
            except PermissionError:
                return Static(
                    f"{ContentStr.permission_denied} for {file_path}",
                    classes=Tcss.removed,
                )
            except UnicodeDecodeError:
                return Static(
                    f"{ContentStr.cannot_decode} for {file_path}", classes=Tcss.removed
                )
            except OSError:
                return Static(
                    f"{ContentStr.read_error} for {file_path}", classes=Tcss.removed
                )
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

    def _mount_and_cache_file_container(
        self, path: "Path", widgets: Static | TextArea
    ) -> None:
        if path in CMD.managed_files or (
            path.is_file() and self.ids.canvas_name == TabName.add
        ):
            self.dir_contents_container.display = False
            self.file_contents_container.display = True
            self.current_file_container.display = False

            # Create a new container for this file to isolate scrolling
            new_container = ScrollableContainer()
            self.file_contents_container.mount(new_container)
            new_container.mount(widgets)

            self.file_cache[path] = new_container
            self.current_file_container = new_container
            self._set_border_title()

    def _remove_and_mount_dir_container_children(
        self, widgets: list[Static | Label]
    ) -> None:
        container = self.query_one(
            self.ids.container.dir_contents_q, ScrollableContainer
        )
        container.remove_children()
        container.mount(*widgets)
        self._set_border_title()

    def watch_show_path(self, show_path: Path) -> None:
        if show_path in self.file_cache:
            if show_path in CMD.managed_files or (
                show_path.is_file() and self.ids.canvas_name == TabName.add
            ):
                self.dir_contents_container.display = False
                self.file_contents_container.display = True
                self.current_file_container.display = False

                cached_container = self.file_cache[show_path]
                cached_container.display = True
                self.current_file_container = cached_container
            elif (
                show_path in CMD.managed_dirs or show_path == CMD.dest_dir
            ) and self.ids.canvas_name != TabName.add:
                self.dir_contents_container.display = True
                self.file_contents_container.display = False
                self.dir_contents_container.remove_children()
                self.dir_contents_container.mount(
                    *self.dir_nodes[show_path].dir_widgets
                )
            elif self.ids.canvas_name == TabName.add and show_path.is_dir():
                self.dir_contents_container.display = True
                self.file_contents_container.display = False
                self.dir_contents_container.remove_children()
                self.dir_contents_container.mount(
                    *self._create_add_dir_contents(show_path)
                )
            self._set_border_title()
            return
        is_managed_file = show_path in CMD.managed_files
        # Show file contents (ApplyTab/ReAddTab/AddTab)
        if show_path in CMD.managed_files or (
            show_path.is_file() and self.ids.canvas_name == TabName.add
        ):
            widget = self._create_file_contents(
                file_path=show_path, managed=is_managed_file
            )
            self._mount_and_cache_file_container(show_path, widget)
        # Managed directories (ApplyTab/ReAddTab)
        elif (
            show_path in CMD.managed_dirs or show_path == CMD.dest_dir
        ) and self.ids.canvas_name != TabName.add:
            widgets = self.dir_nodes[show_path].dir_widgets
            self._remove_and_mount_dir_container_children(widgets)
        # Unmanaged directories (AddTab)
        elif show_path.is_dir() and self.ids.canvas_name == TabName.add:
            widgets = self._create_add_dir_contents(show_path)
            self._remove_and_mount_dir_container_children(widgets)
        else:
            self._mount_and_cache_file_container(
                show_path, Static("unknown", classes=Tcss.removed)
            )
        self._set_border_title()
