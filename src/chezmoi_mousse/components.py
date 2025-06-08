"""Contains classes used components by the widgets in main_tabs.py.

These classes
- inherit directly from built in textual widgets
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't call any query methods
- don't apply tcss classes
"""

import re
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
from chezmoi_mousse import BULLET
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import unwanted
from chezmoi_mousse.mouse_types import TabLabel


class GitLog(DataTable):
    """DataTable widget to display the output of the `git log` command, either
    for a specific path or the chezmoi repository as a whole.

    Does not call the git command directly, calls it through chezmoi.
    """

    # focussable  https://textual.textualize.io/widgets/data_table/

    path: reactive[Path | None] = reactive(None, init=False)

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
        auto_warning = ""
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            auto_warning = '"Auto Commit" is enabled: added file(s) will also be committed.'
        elif chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            auto_warning = '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed to the remote.'

        self.update(
            Content.from_markup(f"[$text-warning italic]{auto_warning}[/]")
        )


class PathView(RichLog):
    # focussable https://textual.textualize.io/widgets/rich_log/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)
    tab: reactive[TabLabel] = reactive("Apply", init=False)

    def on_mount(self) -> None:
        text = "Click a file or directory, \nto show its contents."
        self.write(Text(text, style="dim"))

    def write_managed_dirs_in_dir(self) -> None:
        assert isinstance(self.path, Path)
        managed_dirs: list[Path] = chezmoi.managed_dir_paths_in_dir(self.path)
        if managed_dirs:
            self.write("\nManaged sub dirs:")
            for p in managed_dirs:
                self.write(str(p))

    def write_managed_files_in_dir(self) -> None:
        assert isinstance(self.path, Path)
        managed_files: list[Path] = chezmoi.managed_file_paths_in_dir(
            self.path
        )
        if managed_files:
            self.write("\nManaged files:")
            for p in managed_files:
                self.write(str(p))

    def write_unmanaged_files_in_dir(self) -> None:
        assert isinstance(self.path, Path)
        unmanaged_files: list[Path] = chezmoi.run.unmanaged_in_dir(self.path)
        if unmanaged_files:
            self.write("\nUnmanaged files:")
            self.write('(switch to "AddTab" to add files)')
            for p in unmanaged_files:
                self.write(str(p))

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

            if self.tab == "Add":
                self.write(
                    '(switch to "Apply" or "ReAdd" tab to apply or re-add)'
                )
                self.write_managed_files_in_dir()
                self.write_managed_dirs_in_dir()

        except OSError as error:
            text = Text(f"Error reading {self.path}: {error}")
            self.write(text)

    def watch_path(self) -> None:
        if self.path is not None:
            self.clear()
            self.update_path_view()


class DiffView(RichLog):
    # not focussable https://textual.textualize.io/widgets/static/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab: TabLabel, **kwargs) -> None:
        """Initialize the DiffView for either Apply or Re-Add tab."""
        self.tab: TabLabel = tab
        super().__init__(**kwargs)

    def on_mount(self) -> None:
        self.write(
            Text("Click a file  with status to show the diff.", style="dim")
        )

    def watch_path(self) -> None:
        self.clear()

        diff_output: list[str]
        status_files = chezmoi.status_paths[self.tab].files

        if self.path not in status_files:
            self.write(
                Text(
                    f"No diff available for {self.path}, file not present in chezmoi status output.",
                    style="dim",
                )
            )
            return

        if self.tab == "Apply":
            diff_output = chezmoi.run.apply_diff(self.path)
        elif self.tab == "Re-Add":
            diff_output = chezmoi.run.re_add_diff(self.path)
        else:
            self.write(Text(f"Unknown tab: {self.tab}", style="dim"))
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
                self.write(Text(BULLET + line, style="dim"))


@dataclass
class NodeData:
    path: Path
    found: bool
    is_file: bool
    status: str


class ManagedTree(Tree[NodeData]):
    """Shows the tree widget on the left for Apply and Re-Add tabs."""

    unchanged: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab, flat_list=False, **kwargs) -> None:
        self.tab: TabLabel = tab
        self.flat_list: bool = flat_list
        self.suspend_user_state_save: bool = False
        super().__init__(label="root", **kwargs)
        self.root.data = NodeData(
            # act as if chezmoi.dest_dir always has a modified status
            path=chezmoi.dest_dir,
            found=True,
            is_file=False,
            status="M",
        )

    def on_mount(self) -> None:
        self.node_colors = {
            "Dir": theme.vars["text-primary"],
            "D": theme.vars["text-error"],
            "A": theme.vars["text-success"],
            "M": theme.vars["text-warning"],
        }
        self.guide_depth = 3
        self.show_root = False
        if not self.flat_list:
            self.add_nodes(self.root)
            self.add_leaves(self.root)
        elif self.flat_list:
            self.add_flat_leaves()

    def show_dir_node(self, node_data: NodeData) -> bool:
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

        status_files = chezmoi.status_paths[self.tab].files

        if not self.unchanged:
            return any(f in status_files for f in managed_in_dir_tree)
        elif self.unchanged:
            # Show if this is a managed dir, even if empty
            return (
                bool(managed_in_dir_tree)
                or node_data.path in chezmoi.managed_dir_paths
            )
        return False

    def show_file_node(self, node_data: NodeData) -> bool:
        if not node_data.is_file:
            raise ValueError(
                f"Expected a file node, got {node_data.path} instead."
            )
        if not self.unchanged:
            return node_data.status != "X"
        return True

    def style_label(self, node_data: NodeData) -> Text:
        italic = False if node_data.found else True
        if node_data.status != "X":
            style = Style(
                color=self.node_colors[node_data.status], italic=italic
            )
        elif node_data.is_file:
            style = "dim"
        else:
            style = self.node_colors["Dir"]
        return Text(node_data.path.name, style=style)

    def add_leaves(self, tree_node: TreeNode) -> None:
        current_leafs = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, NodeData) and leaf.data.is_file
        ]
        for leaf in current_leafs:
            leaf.remove()

        status_code = "X"
        assert isinstance(tree_node.data, NodeData)
        file_paths = chezmoi.managed_file_paths_in_dir(tree_node.data.path)
        status_files = chezmoi.status_paths[self.tab].files
        for file_path in file_paths:
            if file_path in status_files:
                status_code = status_files[file_path]
            node_data = NodeData(
                path=file_path,
                found=file_path.exists(),
                is_file=True,
                status=status_code,
            )
            if self.show_file_node(node_data):
                node_label = self.style_label(node_data)
                tree_node.add_leaf(label=node_label, data=node_data)

    def add_flat_leaves(self) -> None:
        status_files = chezmoi.status_paths[self.tab].files
        for file_path in status_files:
            node_data = NodeData(
                path=file_path,
                found=file_path.exists(),
                is_file=True,
                status=status_files[file_path],
            )
            node_label = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

        if self.unchanged:
            for file_path in chezmoi.managed_file_paths_without_status:
                node_data = NodeData(
                    path=file_path,
                    found=file_path.exists(),
                    is_file=True,
                    status="X",
                )
                node_label = self.style_label(node_data)
                self.root.add_leaf(label=node_label, data=node_data)

    def add_nodes(self, tree_node: TreeNode) -> None:
        assert isinstance(tree_node.data, NodeData)
        dir_paths = chezmoi.managed_dir_paths_in_dir(tree_node.data.path)
        status_dirs = chezmoi.status_paths[self.tab].dirs

        # Remove directory nodes that no longer match the filter
        for child in list(tree_node.children):
            if (
                isinstance(child.data, NodeData)
                and not child.data.is_file
                and not self.show_dir_node(child.data)
            ):
                child.remove()

        # Add directory nodes that now match the filter
        for dir_path in dir_paths:
            status_code = "X"
            if dir_path in status_dirs:
                status_code = status_dirs[dir_path]
            node_data = NodeData(
                path=dir_path,
                found=dir_path.exists(),
                is_file=False,
                status=status_code,
            )
            # Only add if not already present and should be shown
            if self.show_dir_node(node_data) and dir_path not in [
                child.data.path
                for child in tree_node.children
                if isinstance(child.data, NodeData) and not child.data.is_file
            ]:
                node_label = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        event.stop()
        self.add_nodes(event.node)
        self.add_leaves(event.node)

    def get_expanded_nodes(self) -> list[TreeNode]:
        """Recursively get all current expanded nodes in the tree, always
        including the root node."""
        nodes = [self.root]  # Always start with the root node

        def collect_nodes(current_node: TreeNode) -> list[TreeNode]:
            expanded = []
            for child in current_node.children:
                if child.is_expanded:
                    expanded.append(child)
                    expanded.extend(collect_nodes(child))
            return expanded

        nodes.extend(collect_nodes(self.root))
        return nodes

    def expand_all_nodes_below(self, node_to_expand: TreeNode) -> None:

        def recurse(node: TreeNode):
            self.add_nodes(node)
            self.add_leaves(node)

            for child in node.children:
                recurse(child)

            recurse(node_to_expand)

    def watch_unchanged(self) -> None:
        """Update the visible nodes based on the "show unchanged" filter."""

        # the switch is disabled when the tree is flat
        if self.flat_list:
            return

        for node in self.get_expanded_nodes():
            self.add_nodes(node)
            self.add_leaves(node)

    def watch_expand_all(self) -> None:
        self.notify("not yet implemented")


class FilteredDirTree(DirectoryTree):
    """Provides a fast DirectoryTree to explore any path in the destination
    directory which can be added to the chezmoi repository."""

    unmanaged_dirs = reactive(False)
    unwanted = reactive(False)

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
            extension = re.match(r"\.[^.]*$", path.name)
            if extension in unwanted["files"]:
                return True
        return False
