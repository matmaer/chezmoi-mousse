from enum import StrEnum
from pathlib import Path

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static, TextArea
from textual.widgets.text_area import BUILTIN_LANGUAGES

from chezmoi_mousse import (
    CMD,
    AppIds,
    AppType,
    DirNode,
    ReadCmd,
    StatusCode,
    TabName,
    Tcss,
)

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

    show_path: reactive["Path | None"] = reactive(None)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.contents, classes=Tcss.border_title_top)
        self.canvas_name = ids.canvas_name
        self.cache: dict[Path, ScrollableContainer] = {}
        self.current_container: ScrollableContainer | None = None

    def on_mount(self) -> None:
        self.border_title = f" {self.app.dest_dir} "

    @property
    def dir_nodes(self) -> dict[Path, DirNode]:
        if self.canvas_name == TabName.apply:
            return self.app.apply_dir_nodes
        else:
            return self.app.re_add_dir_nodes

    @property
    def node_colors(self) -> dict[str, str]:
        return {
            StatusCode.Added: self.app.theme_variables["text-success"],
            StatusCode.Deleted: self.app.theme_variables["text-error"],
            StatusCode.Modified: self.app.theme_variables["text-warning"],
            StatusCode.No_Change: self.app.theme_variables["warning-darken-2"],
            StatusCode.Run: self.app.theme_variables["error"],
            StatusCode.No_Status: self.app.theme_variables["text-secondary"],
        }

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
            try:
                to_show = CMD.read(ReadCmd.cat, path_arg=file_path).std_out
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

    def _create_dir_contents(self, dir_path: Path) -> list[Static | Label]:
        widgets: list[Static | Label] = []
        dir_node: DirNode = self.dir_nodes[dir_path]
        if dir_node.real_status_dirs_in:
            widgets.append(
                Label(
                    "Contains directoiries with a status",
                    classes=Tcss.sub_section_label,
                )
            )
            for path, status in dir_node.real_status_dirs_in.items():
                widgets.append(Static(f"[{self.node_colors[status]}]{path}[/]"))
        if dir_node.status_files_in:
            widgets.append(
                Label("Contains files with a status", classes=Tcss.sub_section_label)
            )
            for path, status in dir_node.status_files_in.items():
                widgets.append(Static(f"[{self.node_colors[status]}]{path}[/]"))
        if dir_path in self.app.x_dirs_with_status_children:
            nested_status_paths = [
                p
                for p in self.app.status_paths
                if p.is_relative_to(dir_path)
                and p not in dir_node.real_status_dirs_in
                and p not in dir_node.tree_status_dirs_in
                and p not in dir_node.status_files_in
                and p != dir_path
            ]
            # only show if nested_status_paths is not empty
            if nested_status_paths:
                widgets.append(
                    Label(
                        "Contains nested paths with a status",
                        classes=Tcss.sub_section_label,
                    )
                )
                for path in sorted(nested_status_paths):
                    widgets.append(Static(f"[dim]{path}[/]"))

        if not dir_node.tree_status_dirs_in and not dir_node.status_files_in:
            if dir_node.tree_status_dirs_in:
                widgets.append(
                    Label(
                        "Contains nested paths with a status",
                        classes=Tcss.sub_section_label,
                    )
                )
                return widgets
            widgets.append(
                Label(
                    f"{dir_path} contains no status paths",
                    classes=Tcss.sub_section_label,
                )
            )
        return widgets

    def _cache_container(
        self, path: Path, *widgets: Static | TextArea | Label
    ) -> ScrollableContainer:
        container = ScrollableContainer()
        self.mount(container)
        if widgets:
            container.mount_all(widgets)
        self.cache[path] = container
        return container

    def watch_show_path(self) -> None:
        if self.show_path is None:
            self.show_path = self.app.dest_dir
            widgets = self._create_dir_contents(self.show_path)
            self._cache_container(self.show_path, *widgets)

        elif self.show_path not in self.cache:
            # Managed files (ApplyTab/ReAddTab)
            if self.show_path in self.app.managed_files:
                widget = self._create_file_contents(
                    file_path=self.show_path, managed=True
                )
                self._cache_container(self.show_path, widget)
            # Managed directories (ApplyTab/ReAddTab)
            elif self.show_path in self.app.managed_dirs:
                widgets = self._create_dir_contents(dir_path=self.show_path)
                container = self._cache_container(self.show_path, *widgets)
                self.mount(container)
                self.cache[self.show_path] = container
            # Unmanaged files (AddTab)
            elif self.show_path.is_file():
                widget = self._create_file_contents(
                    file_path=self.show_path, managed=False
                )
                self._cache_container(self.show_path, widget)
            # Unmanaged directories (AddTab)
            elif self.show_path.is_dir():
                widget = Static(f"{self.show_path} is a directory not managed.")
                self._cache_container(self.show_path, widget)
            else:
                return

        if self.show_path != self.app.dest_dir:
            self.border_title = f" {self.show_path.name} "
        # Hide current container, show the selected one
        if self.current_container is not None:
            self.current_container.display = False
        self.cache[self.show_path].display = True
        self.current_container = self.cache[self.show_path]
