"""Contains classes used as reused components by the widgets in mousse.py."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll
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


class PathView(RichLog):
    """RichLog widget to display the content of a file with highlighting."""

    path: reactive[Path | None] = reactive(None)

    def __init__(self, path: Path | None = None, **kwargs) -> None:
        super().__init__(
            auto_scroll=False, highlight=True, classes="file-preview", **kwargs
        )
        self.path = path

    def on_mount(self) -> None:
        if self.path is None or not isinstance(self.path, Path):
            self.write(" Select a file to view its content.")
        else:
            truncated = ""
            try:
                if self.path.stat().st_size > 150 * 1024:
                    truncated = (
                        "\n\n------ File content truncated to 150 KiB ------\n"
                    )
            except PermissionError as error:
                self.write(error.strerror)
                return
            except FileNotFoundError as error:
                # FileNotFoundError is raised both when a file or a directory
                # does not exist
                if self.path in chezmoi.managed_file_paths:
                    self.write(chezmoi.cat(str(self.path)))
                    return
                elif self.path in chezmoi.managed_dir_paths:
                    text = [
                        "The directory is managed, and does not exist on disk.",
                        f'Output from "chezmoi status {self.path}"',
                        f"{chezmoi.status(str(self.path))}",
                    ]
                    self.write("\n".join(text))
                    return
                else:
                    # a file or dir that doesn't exist and is not managed
                    # should not be displayed in the UI, so raise
                    raise error
            try:
                with open(self.path, "rt", encoding="utf-8") as file:
                    file_content = file.read(150 * 1024)
                    if not file_content.strip():
                        self.write("File contains only whitespace")
                    else:
                        self.write(file_content + truncated)

            except IsADirectoryError:
                self.write(f"Directory: {self.path}")
                return

            except UnicodeDecodeError:
                text = f"{self.path} cannot be decoded as UTF-8."
                self.write(f"{self.path} cannot be decoded as UTF-8.")
                return

            except OSError as error:
                text = Content(f"Error reading {self.path}: {error}")
                self.write(text)

    def watch_path(self) -> None:
        if self.path is not None:
            self.clear()
            self.on_mount()
            self.border_title = f" {self.path.relative_to(chezmoi.dest_dir)} "
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

    include_unmanaged_dirs = reactive(False)
    filter_unwanted = reactive(False)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = chezmoi.managed_dir_paths
        managed_files = chezmoi.managed_file_paths

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
                    and not self.is_unwanted_path(p)
                    and p not in managed_files
                )
                or (
                    p.is_dir()
                    and not self.is_unwanted_path(p)
                    and p in managed_dirs
                )
            )
        # Switches: Green - Red
        elif self.include_unmanaged_dirs and not self.filter_unwanted:
            return (
                p
                for p in paths
                if p not in managed_files and not self.is_unwanted_path(p)
            )
        # Switches: Red - Green
        elif not self.include_unmanaged_dirs and self.filter_unwanted:
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
        elif self.include_unmanaged_dirs and self.filter_unwanted:
            return (
                p
                for p in paths
                if p.is_dir() or (p.is_file() and p not in managed_files)
            )
        else:
            return paths

    def is_unwanted_path(self, path: Path) -> bool:
        if path.is_dir():
            if path.name in unwanted["dirs"]:
                return True
        if path.is_file():
            extension = re.match(r"\.[^.]*$", path.name)
            if extension in unwanted["files"]:
                return True
        return False


@dataclass
class NodeData:
    path: Path
    found: bool
    is_file: bool
    status: str


class ManagedTree(Tree[NodeData]):

    only_missing: reactive[bool] = reactive(False, init=False)
    include_unchanged_files: reactive[bool] = reactive(False, init=False)

    # TODO: default color should be updated on theme change
    node_colors = {
        "Dir": "#57A5E2",  # text-primary
        "D": "#D17E92",  # text-error
        "A": "#8AD4A1",  # text-success
        "M": "#FFC473",  # text-warning
    }

    def __init__(
        self,
        status_files: dict[Path, str],
        status_dirs: dict[Path, str],
        **kwargs,
    ) -> None:
        super().__init__(
            label="initial root", classes="any-tree managed-tree", **kwargs
        )
        self.status_files: dict[Path, str] = status_files
        self.status_dirs: dict[Path, str] = status_dirs

    def on_mount(self) -> None:
        print(f"Mounting {self.__class__.__name__} tree")
        self.show_root = False
        self.border_title = f" {chezmoi.dest_dir} "
        # give root node status R so it's not considered having status "X"
        self.root.data = NodeData(
            path=chezmoi.dest_dir, found=True, is_file=False, status="R"
        )
        self.root.label = str(chezmoi.dest_dir)
        self.root.expand()

    def show_dir_node(self, node_data: NodeData) -> bool:
        """Check if a directory node should be displayed according to the
        current filter settings, including if any subdirectory contains a leaf
        that potentially could include a leaf to display."""

        if node_data.is_file:
            raise ValueError(
                f"Expected a dir node, got {node_data.path} instead."
            )

        if node_data.path == chezmoi.dest_dir:
            return True

        all_files = [
            f
            for f in chezmoi.managed_file_paths
            if node_data.path in f.parents
        ]

        if not self.include_unchanged_files and not self.only_missing:
            return any(f in self.status_files for f in all_files)
        elif self.include_unchanged_files and not self.only_missing:
            return bool(all_files)
        elif not self.include_unchanged_files and self.only_missing:
            return any(
                f in self.status_files and not f.exists() for f in all_files
            )
        elif self.include_unchanged_files and self.only_missing:
            # Not implemented yet
            return False
        return False

    def show_file_node(self, node_data: NodeData) -> bool:
        """Check if a file node should be displayed according to the current
        filter settings."""
        if not node_data.is_file:
            raise ValueError(
                f"Expected a file node, got {node_data.path} instead."
            )

        # include_unchanged_files=False and only_missing=False
        if not self.include_unchanged_files and not self.only_missing:
            return node_data.status != "X"
        # include_unchanged_files=False and only_missing=True
        if not self.include_unchanged_files and self.only_missing:
            return node_data.status != "X" and not node_data.found
        # include_unchanged_files=True and only_missing=True
        if self.include_unchanged_files and self.only_missing:
            return not node_data.found or node_data.status == "X"
        # include_unchanged_files=True and only_missing=False
        return True

    def get_current_dir_nodes(
        self, mode: Literal["expanded", "collapsed", "all"]
    ) -> list[TreeNode]:
        """Recursively get all current dir nodes in the tree, depending on the
        mode.

        mode: "expanded" | "collapsed" | "all"
        """

        def collect_nodes(node: TreeNode) -> list[TreeNode]:
            nodes = []
            for child in node.children:
                assert isinstance(child.data, NodeData)
                if not child.data.is_file:
                    if mode == "collapsed" and child.is_collapsed:
                        nodes.append(child)
                    elif mode == "expanded" and child.is_expanded:
                        nodes.append(child)
                    elif mode == "all":
                        nodes.append(child)
                    # Recurse into directory children
                    nodes.extend(collect_nodes(child))
            return nodes

        return collect_nodes(self.root)

    def style_label(self, node_data: NodeData) -> Text:
        assert isinstance(node_data, NodeData)
        """Color node based on being a file, directary and its status."""
        italic = False if node_data.found else True
        if node_data.status != "X":  # files with a status
            style = Style(
                color=self.node_colors[node_data.status], italic=italic
            )
        elif node_data.is_file:
            style = "dim"
        else:  # format a directory node without status
            style = self.node_colors["Dir"]
        return Text(node_data.path.name, style=style)

    def add_leaves(self, tree_node: TreeNode) -> None:
        """Uses a list of NodeData objects provided by the files_nodes_data
        parameter, to add to the provided tree_node parameter  if the tree_node
        doesn't already contain a node with this path."""

        current_leafs = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, NodeData) and leaf.data.is_file
        ]
        for leaf in current_leafs:
            leaf.remove()

        assert isinstance(tree_node.data, NodeData)
        file_paths = chezmoi.managed_file_paths_in_dir(
            tree_node.data.path, only_with_status=False
        )

        # filter file_nodes_data with show_file_node
        file_nodes_data = [
            node_data
            for node_data in self.create_files_data(file_paths)
            if self.show_file_node(node_data)
        ]

        for node_data in file_nodes_data:
            if self.show_file_node(node_data) and node_data.is_file:
                node_label = self.style_label(node_data)
                tree_node.add_leaf(label=node_label, data=node_data)

    def add_nodes(self, tree_node: TreeNode) -> None:
        """Uses a list of NodeData objects in provided by the dir_nodes_data
        parameter, to add to the provided tree_node parameter if the tree_node
        doesn't already contain a node with this path."""

        assert isinstance(tree_node.data, NodeData)

        dir_paths = chezmoi.managed_dir_paths_in_dir(tree_node.data.path)
        dir_nodes_data: list[NodeData] = self.create_dirs_data(dir_paths)

        # filter dir_nodes_data with show_dir_node
        dir_nodes_data = [
            node_data
            for node_data in dir_nodes_data
            if self.show_dir_node(node_data)
        ]

        current_child_paths = [
            node.data.path
            for node in tree_node.children
            if isinstance(node.data, NodeData)
        ]
        for node_data in dir_nodes_data:
            if (
                self.show_dir_node(node_data)
                and node_data.path not in current_child_paths
            ):
                node_label = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

    def create_files_data(self, file_paths: list[Path]) -> list[NodeData]:
        """Creates a list of NodeData objects from the provided list of
        directory paths provided by the file_paths parameter."""
        result: list[NodeData] = []
        for file_path in file_paths:
            if file_path in self.status_files:
                status_code = self.status_files[file_path]
            else:
                status_code = "X"
            node_data = NodeData(
                path=file_path,
                found=file_path.exists(),
                is_file=True,
                status=status_code,
            )
            result.append(node_data)
        return result

    def create_dirs_data(self, dir_paths: list[Path]) -> list[NodeData]:
        result: list[NodeData] = []
        """Creates a list of NodeData objects from the list of directory paths
        provided by the dir_paths parameter."""
        for dir_path in dir_paths:
            if dir_path in self.status_dirs:
                status_code = self.status_dirs[dir_path]
            else:
                status_code = "X"
            node_data = NodeData(
                path=dir_path,
                found=dir_path.exists(),
                is_file=False,
                status=status_code,
            )
            result.append(node_data)
        return result

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        print(f"Node expanded: {event.node.data}")
        self.add_nodes(event.node)
        self.add_leaves(event.node)

    # def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
    #     print(f"Node collapsed: {event.node.data}")
    #     event.node.remove_children()

    # update nodes when the filter switches are changed
    def update_visible_nodes(self) -> None:
        """Update the visible nodes in the tree based on the current filter
        settings."""
        expanded_nodes = self.get_current_dir_nodes(mode="expanded")
        for node in expanded_nodes:
            self.add_nodes(node)
            self.add_leaves(node)

    def watch_only_missing(self) -> None:
        print(f"new value for only_missing in {self} = {self.only_missing}")
        self.update_visible_nodes()

    def watch_include_unchanged_files(self) -> None:
        print(
            f"new value for include_changed_files in {self} = {self.include_unchanged_files}"
        )
        self.update_visible_nodes()


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


class FilterBar(VerticalGroup):

    class FilterSwitch(HorizontalGroup):
        """A switch, a label and a tooltip."""

        def __init__(
            self, switch_data: dict[str, str], switch_id: str
        ) -> None:
            super().__init__(classes="filter-container")
            self.switch_data = switch_data
            self.switch_id = switch_id

        def compose(self) -> ComposeResult:
            yield Switch(id=self.switch_id, classes="filter-switch")
            yield Label(self.switch_data["label"], classes="filter-label")
            yield Label("(?)", classes="filter-tooltip").with_tooltip(
                tooltip=self.switch_data["tooltip"]
            )

    def __init__(self, filter_key: str, tab_filters_id: str) -> None:
        self.filter_key = filter_key
        self.tab_switches: list[HorizontalGroup] = []
        super().__init__(id=tab_filters_id)

    def on_mount(self) -> None:
        self.tab_switch_data = {
            f"{self.filter_key}_{key}": value
            for key, value in filter_switch_data.items()
            if self.filter_key in value.get("filter_keys", [])
        }
        self.tab_switches = [
            FilterBar.FilterSwitch(switch_data, switch_id)
            for switch_id, switch_data in self.tab_switch_data.items()
        ]
        self.refresh(recompose=True)

    def compose(self) -> ComposeResult:
        yield from self.tab_switches
