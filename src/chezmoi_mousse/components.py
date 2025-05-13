"""Contains classes used as re-used components by the widgets in mousse.py"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Container,
    HorizontalGroup,
    VerticalGroup,
    VerticalScroll,
)
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import (
    Collapsible,
    DirectoryTree,
    Label,
    RichLog,
    Static,
    Switch,
    Tree,
)
from textual.widgets.tree import TreeNode

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import filter_switch_data, status_info, unwanted


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

    file_path: reactive[Path | None] = reactive(None)

    def __init__(self, file_path: Path | None = None, **kwargs) -> None:
        super().__init__(
            auto_scroll=False, highlight=True, classes="file-preview", **kwargs
        )
        self.file_path = file_path
        self.cat_output: str | None = None

    def on_mount(self) -> None:
        if self.file_path is None:
            self.write(" Select a file to view its content.")

        else:
            truncated = ""
            try:
                if self.file_path.stat().st_size > 150 * 1024:
                    truncated = (
                        "\n\n------ File content truncated to 150 KiB ------\n"
                    )
            except (PermissionError, FileNotFoundError, OSError) as error:
                if FileNotFoundError:
                    if self.file_path in chezmoi.managed_file_paths:
                        self.cat_output = chezmoi.cat(str(self.file_path))
                else:
                    self.write(error.strerror)
            try:
                if self.cat_output:
                    self.write(self.cat_output)
                else:
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

    def watch_file_path(self) -> None:
        if self.file_path is not None:
            self.clear()
            self.on_mount()
            self.border_title = (
                f" {self.file_path.relative_to(chezmoi.dest_dir)} "
            )
        else:
            self.border_title = " no file selected "


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
            if line.startswith("-"):
                colored_lines.append(content.stylize("$text-error"))
            elif line.startswith("+"):
                colored_lines.append(content.stylize("$text-success"))
            else:
                colored_lines.append(content.stylize("dim"))

        self.update(Content("\n").join(colored_lines))


class FilteredDirTree(DirectoryTree):

    include_unmanaged_dirs = reactive(False, always_update=True)
    filter_unwanted = reactive(False, always_update=True)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = chezmoi.managed_dir_paths
        managed_files = chezmoi.managed_file_paths
        self.root.label = f"{chezmoi.dest_dir} (destDir)"

        # Switches: Red - Green (default)
        if not self.include_unmanaged_dirs and not self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent == chezmoi.dest_dir
                    )
                    and not is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not is_unwanted_path(p)
                    and p in managed_dirs
                )
            )
        # Switches: Green - Red
        if self.include_unmanaged_dirs and not self.filter_unwanted:
            return (
                p
                for p in paths
                if p not in managed_files and not is_unwanted_path(p)
            )
        # Switches: Red - Green
        if not self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if (
                    p.is_file()
                    and (
                        p.parent in managed_dirs
                        or p.parent == chezmoi.dest_dir
                    )
                    and p not in managed_files
                )
                or (p.is_dir() and p in managed_dirs)
            )
        # Switches: Green - Green, include all unmanaged paths
        else:
            return (
                p
                for p in paths
                if p.is_dir() or (p.is_file() and p not in managed_files)
            )


@dataclass
class NodeData:
    path: Path
    exists: bool = True
    is_file: bool = False
    status: str = "X"


class ManagedTree(Tree[NodeData]):

    # TODO: default color should be updated on theme change
    node_colors = {
        "Dir": "#57A5E2",  # text-primary
        "D": "#D17E92",  # text-error
        "A": "#8AD4A1",  # text-success
        "M": "#FFC473",  # text-warning
    }

    def __init__(
        self,
        file_paths: list[Path],
        dir_paths: list[Path],
        status_files: dict[Path, str],
        status_dirs: dict[Path, str],
        **kwargs,
    ) -> None:
        root_data = NodeData(path=chezmoi.dest_dir)
        root_label = str(chezmoi.dest_dir)
        super().__init__(
            data=root_data, label=root_label, classes="any-tree", **kwargs
        )
        self.file_paths: list[Path] = file_paths
        self.dir_paths: list[Path] = dir_paths
        self.status_files: dict[Path, str] = status_files
        self.status_dirs: dict[Path, str] = status_dirs

    def print_vars(self) -> None:
        print(f"file_paths: {self.file_paths}")
        print(f"dir_paths: {self.dir_paths}")
        print(f"status_files: {self.status_files}")
        print(f"status_dirs: {self.status_dirs}")

    def color_file(self, file_node: TreeNode) -> None:
        assert isinstance(file_node.data, NodeData)
        """Color file node (leaf) based on its status."""
        if file_node.data.path in self.status_files:
            file_node.set_label(
                Text(
                    f"{file_node.data.path.name}",
                    style=self.node_colors[file_node.data.status],
                )
            )
        else:
            file_node.set_label(
                Text(str(file_node.data.path.name), Style(dim=True))
            )

    def add_child_nodes(self, tree_node: TreeNode) -> None:
        assert isinstance(tree_node.data, NodeData)
        # collect subdirectories to add based on the tree_node parameter
        sub_dirs = [
            d for d in self.dir_paths if d.parent == tree_node.data.path
        ]
        for dir_path in sub_dirs:
            node_data = NodeData(path=dir_path)
            node_label = Text(dir_path.name, style=self.node_colors["Dir"])
            tree_node.add(node_label, node_data)

        # collect files to add based on the tree_node parameter
        file_children = [
            f for f in self.file_paths if f.parent == tree_node.data.path
        ]
        for file_path in file_children:

            node_data = NodeData(
                path=file_path,
                is_file=True,
                status=self.status_files[file_path],
            )
            new_leaf = tree_node.add_leaf(file_path.name, node_data)

            assert isinstance(new_leaf.data, NodeData)

            if new_leaf.data.path in self.status_files:
                self.color_file(new_leaf)

    @on(Tree.NodeExpanded)
    def populate_directory(self, event: Tree.NodeExpanded) -> None:
        print(f"Node expanded: {event.node.label}")
        self.add_child_nodes(event.node)

    @on(Tree.NodeCollapsed)
    def clear_all_children(self, event: Tree.NodeExpanded) -> None:

        print(f"Node collapsed: {event.node.label}")
        event.node.remove_children()


class ApplyTree(ManagedTree):
    """Tree for managing 'apply' operations."""

    only_missing: reactive[bool] = reactive(False, init=False)
    include_unchanged_files: reactive[bool] = reactive(False, init=False)

    def __init__(self) -> None:
        # Pass placeholder values to ManagedTree.__init__()
        super().__init__(
            file_paths=[],
            dir_paths=[],
            status_files={},
            status_dirs={},
            id="apply_tree",
        )
        # Attributes will be initialized in on_mount
        self.file_paths: list[Path] = []
        self.dir_paths: list[Path] = []
        self.status_files: dict[Path, str] = {}
        self.status_dirs: dict[Path, str] = {}

    def on_mount(self) -> None:
        # Initialize paths and status data
        self.file_paths = sorted(list(chezmoi.managed_file_paths))
        self.dir_paths = sorted(list(chezmoi.managed_dir_paths))
        self.status_files: dict[Path, str] = chezmoi.status_paths[
            "apply_files"
        ]
        self.status_dirs: dict[Path, str] = chezmoi.status_paths["apply_dirs"]

        print(f"Mounting {self.__class__.__name__} tree")

        # Default switch values: False False
        if not self.include_unchanged_files and not self.only_missing:
            self.file_paths = [
                f
                for f in self.file_paths
                if f in chezmoi.status_paths["apply_files"]
            ]
            parent_dirs = self.create_parent_dir_list(self.file_paths)
            status_dirs = [d for d in self.dir_paths if d in self.status_dirs]
            self.dir_paths = sorted(parent_dirs + status_dirs)

        # Include all files and directories that are managed
        elif self.include_unchanged_files and not self.only_missing:
            self.file_paths = self.file_paths
            self.dir_paths = self.dir_paths

        # Include all managed paths that are missing or their parents
        elif self.include_unchanged_files and self.only_missing:
            self.file_paths = [
                f
                for f in self.file_paths
                if f in chezmoi.status_paths["apply_files"] and not f.exists()
            ]
            dirs_to_include = self.create_parent_dir_list(self.file_paths)
            managed_dirs_with_status = [
                d for d in self.dir_paths if d in self.status_dirs
            ]
            self.dir_paths = sorted(dirs_to_include + managed_dirs_with_status)

        # Include all files or directories that are missing
        elif not self.include_unchanged_files and self.only_missing:
            self.file_paths = [
                f
                for f in self.file_paths
                if f in chezmoi.status_paths["apply_files"] or not f.exists()
            ]
            self.dir_paths = self.dir_paths

        self.show_root = False
        self.border_title = f" {chezmoi.dest_dir} "
        self.root.expand()

    def create_parent_dir_list(
        self, file_paths_to_process: list[Path]
    ) -> list[Path]:
        """Create a list of all parent directories for the given file paths."""
        assert isinstance(self.root.data, NodeData)
        parent_dirs = set()
        for file_path in file_paths_to_process:
            current_path = file_path.parent
            while current_path != self.root.data.path:
                if current_path not in parent_dirs:
                    parent_dirs.add(current_path)
                current_path = current_path.parent
        return sorted(list(parent_dirs))

    def watch_only_missing(self) -> None:
        print(f"new value for only_missing in {self} = {self.only_missing}")

    def watch_include_unchanged_files(self) -> None:
        print(
            f"new value for include_changed_files in {self} = {self.include_unchanged_files}"
        )


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
            chezmoi.status_paths["apply_files"]
            if self.apply
            else chezmoi.status_paths["re_add_files"]
        )

        for file_path, status_code in status_paths.items():
            rel_path = str(file_path.relative_to(chezmoi.dest_dir))
            title = f"{status_info['code name'][status_code]} {rel_path}"
            self.status_items.append(
                Collapsible(StaticDiff(file_path, self.apply), title=title)
            )
        self.refresh(recompose=True)


class FilterSwitch(HorizontalGroup):
    """A switch, a label and a tooltip."""

    def __init__(self, switch_data: dict[str, str], switch_id: str) -> None:
        super().__init__(classes="filter-container")
        self.switch_data = switch_data
        self.switch_id = switch_id

    def compose(self) -> ComposeResult:
        yield Switch(id=self.switch_id, classes="filter-switch")
        yield Label(self.switch_data["label"], classes="filter-label")
        yield Label("(?)", classes="filter-tooltip").with_tooltip(
            tooltip=self.switch_data["tooltip"]
        )


class TabFilters(VerticalGroup):

    def __init__(self, filter_key: str) -> None:
        self.filter_key = filter_key
        self.tab_switches: list[HorizontalGroup] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield from self.tab_switches

    def on_mount(self) -> None:
        self.tab_switch_data = {
            f"{self.filter_key}_{key}": value
            for key, value in filter_switch_data.items()
            if self.filter_key in value.get("filter_keys", [])
        }
        self.tab_switches = [
            FilterSwitch(switch_data, switch_id)
            for switch_id, switch_data in self.tab_switch_data.items()
        ]
        self.refresh(recompose=True)


class FilterBar(Container):

    def __init__(self, filter_key: str, tab_filters_id: str) -> None:
        self.filter_key = filter_key
        super().__init__(id=tab_filters_id)

    def compose(self) -> ComposeResult:
        yield TabFilters(self.filter_key)
