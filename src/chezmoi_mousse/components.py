"""Contains classes used as re-used components by the widgets in mousse.py"""

import re
from collections.abc import Iterable
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Collapsible, DirectoryTree, RichLog, Static, Tree
from textual.widgets.tree import TreeNode

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
                self.write(error.strerror)

            try:
                with open(self.file_path, "rt", encoding="utf-8") as file:
                    file_content = file.read(150 * 1024)
                    if not file_content.strip():
                        self.write("File contains only whitespace")
                    else:
                        self.write(file_content + truncated)
            except (UnicodeDecodeError, IsADirectoryError) as error:
                if isinstance(error, UnicodeDecodeError):
                    self.write("The file cannot be decoded as UTF-8")
                else:
                    self.write(error.strerror)


class ReactiveFileView(FileView):
    """Reactive version of FileView with reactive file path.
    This is useful because FileView is also used in a non-reactive context
    """

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

    # default color but will be updated on theme change
    node_colors = {
        "Dir": "#57A5E2",  # text-primary
        "D": "#D17E92",  # text-error
        "A": "#8AD4A1",  # text-success
        "M": "#FFC473",  # text-warning
    }

    def __init__(
        self, apply: bool, file_paths: set[Path] = set(), **kwargs
    ) -> None:
        self.apply = apply
        self.file_paths = file_paths
        super().__init__(label="root_node", classes="any-tree", **kwargs)

    def on_mount(self) -> None:
        # Collect all directories (including intermediate ones)
        all_dirs = {dest_dir}
        for file_path in self.file_paths:
            current = file_path.parent
            while current not in all_dirs and current != current.parent:
                all_dirs.add(current)
                current = current.parent

        def add_nodes(parent_node, dir_path):
            # Add directory nodes
            if dir_path == dest_dir:
                parent_node = self.root
                self.root.label = str(dir_path)
            else:
                parent_node = parent_node.add(dir_path.name, dir_path)
                parent_node.set_label(
                    Text(dir_path.name, style=self.node_colors["Dir"])
                )

            # Add files in the current directory
            for file in (f for f in self.file_paths if f.parent == dir_path):
                file_node = parent_node.add_leaf(file.name, file)
                file_node.set_label(Text(str(file.name), Style(dim=True)))

            # Add subdirectories
            for sub_dir in (d for d in all_dirs if d.parent == dir_path):
                add_nodes(parent_node, sub_dir)

        # Build the tree starting from dest_dir
        add_nodes(self.root, dest_dir)
        self.show_root = False
        self.border_title = f" {dest_dir} "
        self.root.expand()

    @on(Tree.NodeExpanded)
    def color_files(self, event: Tree.NodeExpanded) -> None:
        """Color the new visible leaves."""
        event.stop()

        file_nodes: list[TreeNode] = []

        file_nodes = [c for c in event.node.children if not c.children]

        status_paths = (
            chezmoi.apply_status_file_paths
            if self.apply
            else chezmoi.re_add_status_file_paths
        )

        status_nodes = [n for n in file_nodes if n.data in status_paths]

        for node in status_nodes:
            label_text = str(node.label)
            if node.data in status_paths:
                status_code: str = status_paths[node.data]
                new_label = Text(
                    label_text, style=self.node_colors[status_code]
                )
                node.set_label(new_label)


class ApplyTree(ManagedTree):
    """Tree for managing 'apply' operations."""

    not_existing: reactive[bool] = reactive(False)
    changed_files: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        # Initialize with a specific set of file paths for ApplyTree
        super().__init__(
            apply=True, file_paths=chezmoi.managed_file_paths, **kwargs
        )

    def on_mount(self) -> None:
        # Additional setup specific to ApplyTree
        self.file_paths = chezmoi.managed_file_paths

    def watch_not_existing(self) -> None:
        self.notify("The not_existing filter was changed")

    def watch_changed_files(self) -> None:
        self.notify("The changed_files filter was changed")


class ReAddTree(ManagedTree):
    """Tree for managing 're-add' operations."""

    changed_files: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        file_paths = {p for p in chezmoi.managed_file_paths if p.exists()}
        # Initialize with a specific set of file paths for ReAddTree
        super().__init__(apply=False, file_paths=file_paths, **kwargs)

    def on_mount(self) -> None:
        # Additional setup specific to ReAddTree
        self.file_paths = chezmoi.managed_file_paths

    def watch_changed_files(self) -> None:
        self.notify("The changed_files filter was changed")


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
        status_paths = (
            chezmoi.apply_status_file_paths
            if self.apply
            else chezmoi.re_add_status_file_paths
        )

        for file_path, status_code in status_paths.items():
            rel_path = str(file_path.relative_to(dest_dir))
            title = f"{status_info['code name'][status_code]} {rel_path}"
            self.status_items.append(
                Collapsible(StaticDiff(file_path, self.apply), title=title)
            )
        self.refresh(recompose=True)
