"""Contains classes used as reused components by the widgets in mousse.py."""

import re
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import (
    HorizontalGroup,
    Vertical,
    VerticalGroup,
    ScrollableContainer,
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
    TabbedContent,
    TabPane,
    Tree,
)
from textual.widgets.tree import TreeNode

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import filter_switch_data, unwanted


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

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(
            id="path_view",
            auto_scroll=False,
            wrap=False,
            highlight=True,
            classes="file-preview",
        )

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
            except FileNotFoundError:
                # FileNotFoundError is raised both when a file or a directory
                # does not exist
                if self.path in chezmoi.managed_file_paths:
                    file_content = chezmoi.cat(str(self.path))
                    if not file_content.strip():
                        self.write("File contains only whitespace")
                    else:
                        self.write(file_content)
                    return

            if self.path in chezmoi.managed_dir_paths:
                text = [
                    "The directory is managed, and does not exist on disk.",
                    f'Output from "chezmoi status {self.path}"',
                    f"{chezmoi.status(str(self.path))}",
                ]
                self.write("\n".join(text))
                return

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


class StaticDiff(ScrollableContainer):

    new_diff_lines: reactive[list[str]] = reactive([])

    @property
    def allow_maximize(self) -> bool:
        return True

    def compose(self) -> ComposeResult:
        yield Static()

    def watch_new_diff_lines(self) -> None:
        static_diff = self.query_exactly_one(Static)
        diff_output: list[str] = [
            line
            for line in self.new_diff_lines
            if line.strip()  # filter lines containing only spaces
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        ]

        if diff_output:
            max_len = max(len(line) for line in diff_output)
        else:
            max_len = 0
        padded_lines = [line.ljust(max_len) for line in diff_output]
        colored_lines: list[Content] = []
        for line in padded_lines:
            if line.startswith("-"):
                colored_lines.append(Content(line).stylize("$text-error"))
            elif line.startswith("+"):
                colored_lines.append(Content(line).stylize("$text-success"))
            else:
                content = Content("▏" + line)
                colored_lines.append(content.stylize("dim"))
        static_diff.update(Content("\n").join(colored_lines))


class PathViewTabs(Vertical):
    """Two tabs to view the content or the diff of a file."""

    selected_path: reactive[Path | None] = reactive(None)
    diff_lines: reactive[list[str]] = reactive([])

    def compose(self) -> ComposeResult:
        with TabbedContent(id="path_review_tabs", classes="path-view-tabs"):
            with TabPane("Content"):
                yield PathView()
            with TabPane("Diff"):
                yield StaticDiff()

    def watch_selected_path(self) -> None:
        if self.selected_path is None:
            return
        self.query_one(PathView).path = self.selected_path

    def watch_diff_lines(self) -> None:
        self.query_one(StaticDiff).new_diff_lines = self.diff_lines


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


class TreeTitle(VerticalGroup):
    """Create a tree title that looks similar to a TabbedContent Tab Styled in
    gui.tcss to distinguish from a real TabbedContent Tab This is used to match
    the tree or directorytree next to the PathViewTabs."""

    def compose(self) -> ComposeResult:
        yield Static(id="tree_title_text", classes="tree-title-text")
        yield Static(id="tree_title_bars", classes="tree-title-bars")

    def on_mount(self) -> None:
        dest_dir_str = f"{chezmoi.dest_dir}{os.sep}"
        tree_title_text = Content.from_text(dest_dir_str)
        tree_title_bars = "━" * len(dest_dir_str)
        self.query_one("#tree_title_text", Static).update(tree_title_text)
        self.query_one("#tree_title_bars", Static).update(tree_title_bars)
        self.styles.width = len(dest_dir_str)


class PathViewTitle(VerticalGroup):

    path_view_title: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Static(id="path_view_title_text", classes="path-view-title-text")
        yield Static(id="path_view_title_bars", classes="path-view-title-bars")

    def watch_path_view_title(self) -> None:
        path_view_title_text = Content.from_text(self.path_view_title)
        path_view_title_bars = "━" * len(self.path_view_title)
        self.query_one("#path_view_title_text", Static).update(
            path_view_title_text
        )
        self.query_one("#path_view_title_bars", Static).update(
            path_view_title_bars
        )
        self.styles.width = len(self.path_view_title)


class AddDirTree(Vertical):
    def compose(self) -> ComposeResult:
        yield TreeTitle(classes="tree-title")
        yield FilteredDirTree(
            chezmoi.dest_dir, classes="dir-tree", id="filtered_dir_tree"
        )

    def on_mount(self) -> None:
        self.query_one(FilteredDirTree).show_root = False
        dir_tree = self.query_one("#filtered_dir_tree", FilteredDirTree)
        dir_tree.root.label = str(chezmoi.dest_dir)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.query_one("#filtered_dir_tree", FilteredDirTree)
        if event.switch.id == "add_tab_unmanaged":
            add_dir_tree.include_unmanaged_dirs = event.value
            add_dir_tree.reload()
        elif event.switch.id == "add_tab_unwanted":
            add_dir_tree.filter_unwanted = event.value
            add_dir_tree.reload()


@dataclass
class NodeData:
    path: Path
    found: bool
    is_file: bool
    status: str


class ManagedTree(Vertical):

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
        self.status_files: dict[Path, str] = status_files
        self.status_dirs: dict[Path, str] = status_dirs
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield TreeTitle(classes="tree-title")
        yield Tree(label="root")

    def on_mount(self) -> None:

        managed_tree = self.query_exactly_one(Tree)
        managed_tree.guide_depth = 2
        if managed_tree.root.data is None:
            managed_tree.root.data = NodeData(
                path=chezmoi.dest_dir, found=True, is_file=False, status="R"
            )
        # give root node status R so it's not considered having status "X"
        managed_tree.show_root = False
        self.add_nodes(managed_tree.root)
        self.add_leaves(managed_tree.root)

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

        managed_in_dir_tree = [
            f
            for f in chezmoi.managed_file_paths
            if node_data.path in f.parents
        ]

        # include_unchanged_files=False
        if not self.include_unchanged_files:
            return any(f in self.status_files for f in managed_in_dir_tree)

        # include_unchanged_files=False
        elif self.include_unchanged_files:
            return bool(managed_in_dir_tree)
        return False

    def show_file_node(self, node_data: NodeData) -> bool:
        """Check if a file node should be displayed according to the current
        filter settings."""
        if not node_data.is_file:
            raise ValueError(
                f"Expected a file node, got {node_data.path} instead."
            )
        # include_unchanged_files=False
        if not self.include_unchanged_files:
            return node_data.status != "X"
        # include_unchanged_files=True
        return True

    def get_expanded_nodes(self, root_node: TreeNode) -> list[TreeNode]:
        """Recursively get all current expanded nodes in the tree."""

        def collect_nodes(node: TreeNode) -> list[TreeNode]:
            nodes = [root_node]
            for child in node.children:
                if child.is_expanded:
                    nodes.append(child)
                    # Recurse into directory children
                    nodes.extend(collect_nodes(child))
            return nodes

        return collect_nodes(root_node)

    def style_label(self, node_data: NodeData) -> Text:
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
        """Adds a leaf for each file in the tree_node.data.path directory,"""
        current_leafs = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, NodeData) and leaf.data.is_file
        ]
        for leaf in current_leafs:
            leaf.remove()

        assert isinstance(tree_node.data, NodeData)
        file_paths = chezmoi.managed_file_paths_in_dir(tree_node.data.path)

        for file_path in file_paths:
            status_code = "X"
            if file_path in self.status_files:
                status_code = self.status_files[file_path]
            node_data = NodeData(
                path=file_path,
                found=file_path.exists(),
                is_file=True,
                status=status_code,
            )
            if self.show_file_node(node_data):
                node_label = self.style_label(node_data)
                tree_node.add_leaf(label=node_label, data=node_data)

    def add_nodes(self, tree_node: TreeNode) -> None:
        """Adds a node for each directory in the tree_node.data.path
        directory."""

        assert isinstance(tree_node.data, NodeData)
        dir_paths = chezmoi.managed_dir_paths_in_dir(tree_node.data.path)

        current_sub_dir_node_paths = [
            child.data.path
            for child in tree_node.children
            if isinstance(child.data, NodeData) and not child.data.is_file
        ]

        for dir_path in dir_paths:
            status_code = "X"
            if dir_path in self.status_dirs:
                status_code = self.status_dirs[dir_path]
            node_data = NodeData(
                path=dir_path,
                found=dir_path.exists(),
                is_file=False,
                status=status_code,
            )
            if (
                self.show_dir_node(node_data)
                and node_data.path not in current_sub_dir_node_paths
            ):
                node_label = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        if not isinstance(event.node.data, NodeData):
            return
        self.add_nodes(event.node)
        self.add_leaves(event.node)

    def watch_include_unchanged_files(self) -> None:
        """Update the visible nodes in the tree based on the current filter
        settings."""
        root_node = self.query_exactly_one(Tree).root
        expanded_nodes = self.get_expanded_nodes(root_node)
        for node in expanded_nodes:
            self.add_nodes(node)
            self.add_leaves(node)


class ChezmoiStatus(Vertical):

    apply_status: reactive[bool | None] | None = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        with Collapsible(title="Chezmoi Status", id="chezmoi_status_group"):
            yield from self.status_items

    def on_mount(self) -> None:
        # status can be a space so not using str.split() or str.strip()
        status_paths: dict[Path, str] = (
            chezmoi.status_paths["apply_files"]
            if self.apply_status
            else chezmoi.status_paths["re_add_files"]
        )

        # write dict comprehension to create a dict with the file path as key
        # and as value that the command returns, which is a list of strings
        # depending on the apply_status bool, to determine calling chezmoi.apply_diff() or
        # chezmoi.re_add_diff()
        diff_results = {
            file_path: (
                chezmoi.apply_diff(str(file_path))
                if self.apply_status
                else chezmoi.re_add_diff(str(file_path))
            )
            for file_path in status_paths
        }

        self.status_items = []
        for file_path, status_code in status_paths.items():
            title = f"{file_path.relative_to(chezmoi.dest_dir)}: {status_code}"
            static_diff = StaticDiff()
            static_diff.new_diff_lines = diff_results[file_path]
            self.status_items.append(Collapsible(static_diff, title=title))
        self.refresh(recompose=True)


class FilterBar(Vertical):

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

    def __init__(self, filter_key: str) -> None:
        self.filter_key = filter_key
        self.tab_switches: list[HorizontalGroup] = []
        super().__init__(classes="filter-bar")

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield from self.tab_switches

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
