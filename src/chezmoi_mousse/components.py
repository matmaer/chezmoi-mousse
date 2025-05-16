"""Contains classes used as re-used components by the widgets in mousse.py"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
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
        self.include_unchanged_files = False
        self.only_missing = False

    def on_mount(self) -> None:
        print(f"Mounting {self.__class__.__name__} tree")
        self.show_root = False
        self.border_title = f" {chezmoi.dest_dir} "
        self.root.data = NodeData(
            path=chezmoi.dest_dir, found=True, is_file=False, status="X"
        )
        self.root.label = str(chezmoi.dest_dir)
        self.root.expand()

    def get_all_current_nodes(self) -> list[TreeNode]:
        """Get all current nodes in the tree."""

        def collect_nodes(node: TreeNode) -> list[TreeNode]:
            nodes = [node]
            for child in node.children:
                assert isinstance(child.data, NodeData)
                if not child.data.is_file:
                    nodes.append(child)
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

    def add_leaves(
        self, tree_node: TreeNode, file_nodes_data: list[NodeData]
    ) -> None:
        # collect files to add based on the tree_node parameter
        for node_data in file_nodes_data:
            node_label = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def add_nodes(
        self, tree_node: TreeNode, dir_nodes_data: list[NodeData]
    ) -> None:
        # collect files to add based on the tree_node parameter
        for node_data in dir_nodes_data:
            node_label = self.style_label(node_data)
            tree_node.add(label=node_label, data=node_data)

    def create_files_data(self, file_paths: list[Path]) -> list[NodeData]:
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

    def filter_files_data(
        self,
        files_data: list[NodeData],
        include_unchanged_files=False,
        only_missing=False,
    ) -> list[NodeData]:
        """Filter nodes based on the value of the filter switches."""
        result: list[NodeData] = []
        # include_unchanged_files=False and only_missing=False
        if not include_unchanged_files and not only_missing:
            return [_ for _ in files_data if _.status != "X"]
        # include_unchanged_files=False and only_missing=True
        if not include_unchanged_files and only_missing:
            return [_ for _ in files_data if _.found and _.status != "X"]
        # include_unchanged_files=True and only_missing=True
        if include_unchanged_files and only_missing:
            return [_ for _ in files_data if _.found]
        # include_unchanged_files=True and only_missing=False
        return files_data

    def expanded_node_cleanup(self) -> None:
        current_nodes = self.get_all_current_nodes()
        expanded_nodes = [n for n in current_nodes if n.is_expanded]
        for node in expanded_nodes:
            if not node.children:
                node.remove()

    def populate_node(self, node: TreeNode) -> None:
        """Populate the node with files and directories."""
        assert isinstance(node.data, NodeData)

        dir_paths = chezmoi.managed_dir_paths_in_dir(node.data.path)
        dir_nodes_data = self.create_dirs_data(dir_paths)
        # dirs_nodes_data = self.filter_files_data(dirs_nodes_data)

        file_paths = chezmoi.managed_file_paths_in_dir(node.data.path)
        file_nodes_data = self.create_files_data(file_paths)

        self.add_nodes(node, dir_nodes_data)
        self.add_leaves(node, self.filter_files_data(file_nodes_data))

        # self.expanded_node_cleanup()


class ApplyTree(ManagedTree):
    """Tree for 'chezmoi apply' operations."""

    only_missing: reactive[bool] = reactive(False, init=False)
    include_unchanged_files: reactive[bool] = reactive(False, init=False)

    def __init__(self) -> None:
        super().__init__(
            status_files=chezmoi.status_paths["apply_files"],
            status_dirs=chezmoi.status_paths["apply_dirs"],
            id="apply_tree",
        )

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        print(f"Node expanded: {event.node.data}")
        self.populate_node(event.node)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        print(f"Selected node data: {event.node.data}")

    def watch_only_missing(self) -> None:
        print(f"new value for only_missing in {self} = {self.only_missing}")

    def watch_include_unchanged_files(self) -> None:
        print(
            f"new value for include_changed_files in {self} = {self.include_unchanged_files}"
        )


class ReAddTree(ManagedTree):
    """Tree for 'chezmoi re-add' operations."""

    include_unchanged_files: reactive[bool] = reactive(False, init=False)

    def __init__(self) -> None:
        super().__init__(
            status_files=chezmoi.status_paths["re_add_files"],
            status_dirs=chezmoi.status_paths["re_add_dirs"],
            id="re_add_tree",
        )

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        print(f"Node expanded: {event.node.data}")
        self.populate_node(event.node)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        print(f"Selected node data: {event.node.data}")

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
