"""Contains classes used as widgets by the main_tabs.py module.

These classes
- inherit directly from built in textual widgets
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't call any query methods
- don't apply tcss classes
- don't import from main_tabs.py, gui.py or containers.py modules
"""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual.binding import Binding
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import DataTable, DirectoryTree, RichLog, Static, Tree
from textual.widgets.tree import TreeNode

import chezmoi_mousse.theme as theme
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import unwanted
from chezmoi_mousse.id_typing import CharsEnum, ComponentStr, IdMixin, TabEnum


class GitLog(DataTable, IdMixin):
    """DataTable widget to display the output of the `git log` command, either
    for a specific path or the chezmoi repository as a whole.

    Does not call the git command directly, calls it through chezmoi.
    """

    # focussable  https://textual.textualize.io/widgets/data_table/

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(id=self.component_id(ComponentStr.git_log), **kwargs)

    def on_mount(self) -> None:
        self.show_cursor = False
        if self.path is None:
            self.populate_data_table(chezmoi.git_log.list_out)

    def add_row_with_style(self, columns, style):
        row = [Text(cell_text, style=style) for cell_text in columns]
        self.add_row(*row)

    def populate_data_table(self, cmd_output: list[str]) -> None:
        styles = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
        }
        self.add_columns("COMMIT", "MESSAGE")
        for line in cmd_output:
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                self.add_row_with_style(columns, styles["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self.add_row_with_style(columns, styles["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self.add_row_with_style(columns, styles["error"])
            else:
                self.add_row(*columns)

    def watch_path(self) -> None:
        assert isinstance(self.path, Path)
        git_log_output = chezmoi.run.git_log(self.path)
        self.clear(columns=True)
        self.populate_data_table(git_log_output)


class AutoWarning(Static):
    """Shows important information before the user performs a chezmoi.perform
    command which could trigger other commands depending on the chezmoi
    configuration."""

    # not focussable https://textual.textualize.io/widgets/static/

    def on_mount(self) -> None:
        auto_warning = []
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            auto_warning.append(
                '"Auto Commit" is enabled: added file(s) will also be committed.'
            )
        if chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            auto_warning.append(
                '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed to the remote.'
            )
        if chezmoi.autoadd_enabled:
            auto_warning.append(
                '"Auto Add" is enabled: files will be added automatically, don\'t use the GUI while editing files.'
            )
        self.update(
            Content.from_markup(
                f"[$text-warning italic]{' '.join(auto_warning)}[/]"
            )
        )


class PathView(RichLog, IdMixin):
    # focussable https://textual.textualize.io/widgets/rich_log/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            id=self.component_id(ComponentStr.path_view),
            auto_scroll=True,
            wrap=True,
            highlight=True,
            **kwargs,
        )

    def on_mount(self) -> None:
        text = "Click a file or directory, \nto show its contents.\n"
        self.write(Text(text, style="dim"))
        self.write("Current directory:")
        self.write(f"{chezmoi.dest_dir}")
        self.write(Text("(destDir)\n", style="dim"))
        self.write("Source directory:")
        self.write(f"{chezmoi.source_dir}")
        self.write(Text("(sourceDir)", style="dim"))

    def update_path_view(self) -> None:
        assert isinstance(self.path, Path)
        truncated = ""
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated = (
                    "\n\n------ File content truncated to 150 KiB ------\n"
                )
        except PermissionError as error:
            self.write(error.strerror)
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if not file_content.strip():
                    self.write("File contains only whitespace")
                else:
                    self.write(file_content + truncated)

        except UnicodeDecodeError:
            self.write(f"{self.path} cannot be decoded as UTF-8.")
            return

        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.path in chezmoi.managed_file_paths:
                if not chezmoi.run.cat(self.path).strip():
                    self.write("File contains only whitespace")
                else:
                    self.write(chezmoi.run.cat(self.path))
                return

        except IsADirectoryError:
            if self.path in chezmoi.managed_dir_paths:
                self.write(f"Managed directory: {self.path}")
            else:
                self.write(f"Unmanaged directory: {self.path}")

        except OSError as error:
            text = Text(f"Error reading {self.path}: {error}")
            self.write(text)

    def watch_path(self) -> None:
        if self.path is not None:
            self.clear()
            self.update_path_view()


class DiffView(RichLog, IdMixin):
    # not focussable https://textual.textualize.io/widgets/static/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            id=self.component_id(ComponentStr.diff_view), **kwargs
        )
        self.tab_name: str = tab_key.name

    def on_mount(self) -> None:
        self.write(
            Text("Click a file  with status to show the diff.", style="dim")
        )

    def watch_path(self) -> None:
        self.clear()

        diff_output: list[str]
        status_files = chezmoi.managed_status[self.tab_name].files

        if self.path not in status_files:
            self.write(
                Text(
                    f"No diff available for {self.path}, file not present in chezmoi status output.",
                    style="dim",
                )
            )
            return

        if self.tab_name == TabEnum.apply_tab.name:
            diff_output = chezmoi.run.apply_diff(self.path)
        elif self.tab_name == TabEnum.re_add_tab.name:
            diff_output = chezmoi.run.re_add_diff(self.path)
        else:
            self.write(Text(f"Unknown tab: {self.tab_name}", style="dim"))
            return

        if not diff_output:
            self.write(Text(f"chezmoi diff {self.path} returned no output."))
            return

        diff_lines: list[str] = [
            line
            for line in diff_output
            if line.strip()  # filter lines containing only spaces
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        ]

        for line in diff_lines:
            line = line.rstrip("\n")
            if line.startswith("-"):
                self.write(Text(line, theme.vars["text-error"]))
            elif line.startswith("+"):
                self.write(Text(line, theme.vars["text-success"]))
            else:
                self.write(Text(CharsEnum.bullet.value + line, style="dim"))


@dataclass
class NodeData:
    path: Path
    found: bool
    status: str


@dataclass
class DirNodeData(NodeData):
    pass


@dataclass
class FileNodeData(NodeData):
    pass


class TreeBase(Tree[NodeData]):
    """Shows the tree widget on the left for Apply and Re-Add tabs."""

    # unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        self.tab_key = tab_key
        self.tab_name: str = tab_key.name
        self.node_colors = {
            "Dir": theme.vars["text-primary"],
            "D": theme.vars["text-error"],
            "A": theme.vars["text-success"],
            "M": theme.vars["text-warning"],
        }
        root_node_data = DirNodeData(
            path=chezmoi.dest_dir, found=True, status="R"
        )
        super().__init__(label="root", data=root_node_data, **kwargs)

    def on_mount(self) -> None:
        self.guide_depth = 3
        self.show_root = False

    def create_dir_node_data(self, path: Path) -> DirNodeData:
        """Create a DirNodeData instance for a given path."""
        status_code = chezmoi.managed_status[self.tab_name].dirs[path]
        if not status_code:
            status_code = "X"
        found = path.exists()
        return DirNodeData(path=path, found=found, status=status_code)

    def create_file_node_data(self, path: Path) -> FileNodeData:
        """Create a FileNodeData instance for a given path."""
        status_code = chezmoi.managed_status[self.tab_name].files[path]
        found = path.exists()
        return FileNodeData(path=path, found=found, status=status_code)

    def get_expanded_nodes(self) -> list[TreeNode]:
        """Recursively get all current expanded nodes in the tree, always
        including the root node."""
        nodes = [self.root]

        def collect_nodes(current_node: TreeNode) -> list[TreeNode]:
            expanded = []
            for child in current_node.children:
                if child.is_expanded:
                    expanded.append(child)
                    expanded.extend(collect_nodes(child))
            return expanded

        nodes.extend(collect_nodes(self.root))
        return nodes

    def should_show_dir_node(self, dir_path, unchanged: bool) -> bool:
        if not unchanged:
            has_status_files = chezmoi.dir_has_status_files(
                self.tab_key, dir_path
            )
            has_status_dirs = chezmoi.dir_has_status_dirs(
                self.tab_key, dir_path
            )
            return has_status_files or has_status_dirs
        return True

    def add_unchanged_leaves(self, tree_node: TreeNode) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        unchanged_in_dir = chezmoi.files_without_status_in(
            self.tab_key, tree_node.data.path
        )
        for file_path in unchanged_in_dir:
            node_data = self.create_file_node_data(file_path)
            node_label = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def remove_unchanged_leaves(self, tree_node: TreeNode) -> None:
        current_unchanged_leaves = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, FileNodeData) and leaf.data.status == "X"
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_leaves(self, tree_node: TreeNode) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        status_file_paths = chezmoi.files_with_status_in(
            self.tab_key, tree_node.data.path
        )
        for file in status_file_paths:
            node_data = self.create_file_node_data(file)
            node_label = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def add_dir_nodes(self, tree_node: TreeNode, unchanged) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        for dir_path in chezmoi.managed_dirs_in(tree_node.data.path):
            if self.should_show_dir_node(dir_path, unchanged):
                node_data = self.create_dir_node_data(dir_path)
                node_label = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

    def remove_unchanged_dir_nodes(
        self, tree_node: TreeNode, unchanged: bool
    ) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        dir_nodes = [
            dir_node
            for dir_node in tree_node.children
            if isinstance(dir_node.data, DirNodeData)
            and dir_node.data.status == "X"
        ]
        for dir_node in dir_nodes:
            if dir_node.data is not None and not self.should_show_dir_node(
                dir_node.data.path, unchanged
            ):
                dir_node.remove()

    def style_label(self, node_data: NodeData) -> Text:
        italic = False if node_data.found else True
        if node_data.status != "X":
            style = Style(
                color=self.node_colors[node_data.status], italic=italic
            )
        elif isinstance(node_data, FileNodeData):
            style = "dim"
        else:
            style = self.node_colors["Dir"]
        return Text(node_data.path.name, style=style)


class ManagedTree(TreeBase, IdMixin):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            tab_key, id=self.component_id(ComponentStr.managed_tree), **kwargs
        )

    def on_mount(self) -> None:
        self.add_dir_nodes(self.root, self.unchanged)
        self.add_status_leaves(self.root)

    def on_tree_node_expanded(self, event: TreeBase.NodeExpanded) -> None:
        self.add_dir_nodes(event.node, self.unchanged)
        self.add_status_leaves(event.node)
        if self.unchanged:
            self.add_unchanged_leaves(event.node)
        else:
            self.remove_unchanged_leaves(event.node)

    def on_tree_node_collapsed(self, event: TreeBase.NodeExpanded) -> None:
        event.node.remove_children()

    def watch_unchanged(self) -> None:
        for node in self.get_expanded_nodes():
            if self.unchanged:
                self.add_unchanged_leaves(node)
            if not self.unchanged:
                self.remove_unchanged_leaves(node)


class ExpandedTree(TreeBase, IdMixin):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            tab_key, id=self.component_id(ComponentStr.expanded_tree), **kwargs
        )

    def on_mount(self) -> None:
        self.expand_all_nodes(self.root)

    def expand_all_nodes(self, node: TreeNode) -> None:
        """Recursively expand all directory nodes."""
        if (
            node.data
            and isinstance(node.data, DirNodeData)
            and self.should_show_dir_node(node.data.path, self.unchanged)
        ):
            if not node.is_expanded:
                node.expand()
                self.add_dir_nodes(node, self.unchanged)
                self.add_status_leaves(node)
            for child in node.children:
                if child.data and isinstance(child.data, DirNodeData):
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        expanded_nodes = self.get_expanded_nodes()
        for tree_node in expanded_nodes:
            if self.unchanged:
                self.add_unchanged_leaves(tree_node)
            if not self.unchanged:
                self.remove_unchanged_leaves(tree_node)


class FlatTree(TreeBase, IdMixin):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_key: TabEnum, **kwargs) -> None:
        IdMixin.__init__(self, tab_key)
        super().__init__(
            tab_key, id=self.component_id(ComponentStr.flat_tree), **kwargs
        )

    def on_mount(self) -> None:
        for file_path, status in chezmoi.managed_status[
            self.tab_name
        ].files.items():
            if status != "X":
                node_data = self.create_file_node_data(file_path)
                node_label = self.style_label(node_data)
                self.root.add_leaf(label=node_label, data=node_data)

    def add_all_unchanged_files(self) -> None:
        for file_path, status in chezmoi.managed_status[
            self.tab_name
        ].files.items():
            if status == "X":
                node_data = self.create_file_node_data(file_path)
                node_label = self.style_label(node_data)
                self.root.add_leaf(label=node_label, data=node_data)

    def remove_flat_leaves(self) -> None:
        self.remove_unchanged_leaves(self.root)

    def watch_unchanged(self) -> None:
        if self.unchanged:
            self.add_all_unchanged_files()
        elif not self.unchanged:
            self.remove_flat_leaves()


class FilteredDirTree(DirectoryTree):
    """Provides a fast DirectoryTree to explore any path in the destination
    directory which can be added to the chezmoi repository."""

    unmanaged_dirs = reactive(False)
    unwanted = reactive(False)

    def on_mount(self) -> None:
        self.show_root = False
        self.guide_depth = 3

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed_dirs = chezmoi.managed_dir_paths
        managed_files = chezmoi.managed_file_paths

        # Switches: Red - Green (default)
        if not self.unmanaged_dirs and not self.unwanted:
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
        elif self.unmanaged_dirs and not self.unwanted:
            return (
                p
                for p in paths
                if p not in managed_files and not self.is_unwanted_path(p)
            )
        # Switches: Red - Green
        elif not self.unmanaged_dirs and self.unwanted:
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
        elif self.unmanaged_dirs and self.unwanted:
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
            extension = path.suffix
            if extension in unwanted["files"]:
                return True
        return False
