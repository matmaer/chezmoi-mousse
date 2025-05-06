"""Contains classes used as re-used components by the widgets in mousse.py"""

import re
from collections.abc import Iterable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Collapsible, DirectoryTree, RichLog, Static, Tree

from chezmoi_mousse.chezmoi import chezmoi, dest_dir
from chezmoi_mousse.config import status_info, unwanted


def is_unwanted_path(path: Path) -> bool:
    if path.is_dir():
        if path.name in unwanted["dirs"]:
            return True
    if path.is_file():
        extension = re.match(r"\.[^.]*$", path.name)
        if extension in unwanted["files"]:
            return True
    return False


class AutoWarning(Static):

    def on_mount(self) -> None:
        auto_warning = ""
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            auto_warning = '"Auto Commit" is enabled: added file(s) will also be committed.'
        elif chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            auto_warning = '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed to the remote.'

        self.update(
            Content.from_markup(f"[$text-warning italic]{auto_warning}[/]")
        )


class FileView(RichLog):
    """RichLog widget to display the content of a file with highlighting."""

    def __init__(self, file_path: Path | None = None, **kwargs) -> None:
        super().__init__(
            auto_scroll=False, highlight=True, classes="file-preview", **kwargs
        )
        self.file_path = file_path

    def on_mount(self) -> None:
        if self.file_path is None:
            self.write(" Select a file to view its content.")
        elif not self.file_path.exists():
            self.write(f"File does not exist: {self.file_path}")
        else:
            truncated = ""
            try:
                if self.file_path.stat().st_size > 150 * 1024:
                    truncated = (
                        "\n\n------ File content truncated to 150 KiB ------\n"
                    )
            except (PermissionError, FileNotFoundError, OSError) as error:
                self.write(str(error))

            try:
                with open(self.file_path, "rt", encoding="utf-8") as file:
                    file_content = file.read(150 * 1024)
                    if not file_content.strip():
                        self.write("File contains only whitespace")
                    else:
                        self.write(file_content + truncated)
            except (UnicodeDecodeError, IsADirectoryError) as error:
                self.write(str(error))


class ReactiveFileView(FileView):
    """Reactive version of FileView with reactive file path."""

    file_path: reactive[Path | None] = reactive(None)

    def watch_file_path(self) -> None:
        if self.file_path is not None:
            self.clear()
            self.on_mount()
            self.border_title = f" {self.file_path.relative_to(dest_dir)} "
        else:
            self.border_title = " no file selected "


class FileViewCollapsible(Collapsible):
    """Collapsible widget to display the content of a file."""

    def __init__(self, file_path: Path | None = None) -> None:
        self.file_path = file_path
        super().__init__(ReactiveFileView(self.file_path))

    def on_mount(self) -> None:
        if self.file_path is not None:
            self.title = str(self.file_path.relative_to(dest_dir))


class StaticDiff(Static):

    def __init__(self, file_path: Path, apply: bool) -> None:
        self.file_path = file_path
        self.apply = apply
        super().__init__()

    def on_mount(self) -> None:

        diff_output = (
            line
            for line in chezmoi.diff(str(self.file_path), self.apply)
            if line.strip()  # filter lines containing only spaces
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        )

        colored_lines: list[Content] = []
        for line in diff_output:
            content = Content(line)
            if line.startswith("+"):
                colored_lines.append(content.stylize("$text-error"))
            elif line.startswith("-"):
                colored_lines.append(content.stylize("$text-success"))
            else:
                colored_lines.append(content.stylize("dim"))

        self.update(Content("\n").join(colored_lines))


class FilteredDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(True, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = chezmoi.managed_dir_paths
        managed_files = chezmoi.managed_file_paths
        self.root.label = f"{dest_dir} (destDir)"

        # Switches: Red - Green (default)
        if not self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == dest_dir)
                    and not is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not is_unwanted_path(p)
                    and p in managed_dirs
                )
            )
        # Switches: Red - Red
        if not self.include_unmanaged_dirs and not self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (p.parent in managed_dirs or p.parent == dest_dir)
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            )
        # Switches: Green - Green
        if self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if p not in managed_files and not is_unwanted_path(p)
            )
        # Switches: Green - Red , this means the following is true:
        # "self.include_unmanaged_dirs and not self.filter_unwanted"
        return (
            p
            for p in paths
            if p.is_dir() or (p.is_file() and p not in managed_files)
        )


class ManagedTree(Tree):

    def __init__(self, file_paths: set[Path] | None = None, **kwargs) -> None:
        if file_paths is None:
            self.file_paths = chezmoi.managed_file_paths
        else:
            self.file_paths = file_paths
        super().__init__(label=str("root_node"), **kwargs)

    def on_mount(self) -> None:

        # Collect all parent directories, including intermediate ones
        dir_nodes = set()
        for file_path in self.file_paths:
            current = file_path.parent
            while (
                # Stop at the root directory
                current != current.parent
                # Stop if current is dest_dir
                and current != dest_dir
                # Stop if dest_dir is a subdirectory of current
                and not dest_dir.is_relative_to(current)
            ):
                dir_nodes.add(current)
                current = current.parent

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir:
                parent = self.root
                self.root.label = str(dir_path)
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [f for f in self.file_paths if f.parent == dir_path]
            for file in files:
                parent.add_leaf(str(file.parts[-1]), file)
            sub_dirs = [d for d in dir_nodes if d.parent == dir_path]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir)
        self.root.expand()


class ChezmoiStatus(VerticalScroll):

    def __init__(self, apply: bool, **kwargs) -> None:
        # if true, adds apply status to the list, otherwise "re-add" status
        self.apply = apply
        self.status_items: list[Collapsible] = []
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Collapsible(*self.status_items, title="Chezmoi Status")

    def on_mount(self) -> None:
        # status can be a space so not using str.split() or str.strip()
        status_paths = [
            (adm, Path(line[3:]))
            for line in chezmoi.status_files.list_out
            if (adm := line[1] if self.apply else line[0]) in "ADM"
        ]
        for status_code, file_path in status_paths:
            rel_path = str(file_path.relative_to(dest_dir))
            title = f"{status_info["code name"][status_code]} {rel_path}"
            self.status_items.append(
                Collapsible(StaticDiff(file_path, self.apply), title=title)
            )
        self.refresh(recompose=True)
