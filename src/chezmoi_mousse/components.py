"""Contains classes used by the widgets in main_tabs.py.

These classes
- inherit directly from built in textual widgets or can be dataclasses
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't override the parents' init method
- don't call any query methods
- don't apply tcss classes
"""

import re

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich.style import Style
from rich.text import Text
from textual.binding import Binding
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import DataTable, DirectoryTree, RichLog, Static, Tree
from textual.widgets.tree import TreeNode
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import unwanted

# from chezmoi_mousse.mouse_types import


class GitLog(DataTable):
    """DataTable widget to display the output of the `git log` command, either
    for a specific path or the chezmoi repository as a whole.

    Does not call the git command directly, calls it through chezmoi.
    """

    # focussable  https://textual.textualize.io/widgets/data_table/

    path: reactive[Path | None] = reactive(None, init=False)

    # def __init__(self, path: Path | None = None, **kwargs) -> None:
    #     super().__init__(**kwargs)
    #     self.path = path

    def on_mount(self) -> None:
        self.show_cursor = False
        if self.path is None:
            self.populate_data_table(chezmoi.git_log.list_out)

    def populate_data_table(self, cmd_output: list[str]):
        styles = {
            "ok": f"{self.app.current_theme.success}",
            "warning": f"{self.app.current_theme.warning}",
            "error": f"{self.app.current_theme.error}",
            "info": f"{self.app.current_theme.foreground}",
        }
        self.add_columns("COMMIT", "MESSAGE")
        for line in cmd_output:
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                row = [
                    Text(cell_text, style=f"{styles['ok']}")
                    for cell_text in columns
                ]
                self.add_row(*row)
            elif columns[1].split(maxsplit=1)[0] == "Update":
                row = [
                    Text(cell_text, style=f"{styles['warning']}")
                    for cell_text in columns
                ]
                self.add_row(*row)
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                row = [
                    Text(cell_text, style=f"{styles['error']}")
                    for cell_text in columns
                ]
                self.add_row(*row)
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
    """RichLog widget to display the content of a file with highlighting."""

    # focussable https://textual.textualize.io/widgets/rich_log/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)
    tab_id: reactive[str] = reactive("apply_tab", init=False)

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
            text = f"{self.path} cannot be decoded as UTF-8."
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

            if self.tab_id == "add_tab":
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


class DiffView(Static):
    """Shows the diff between the destination and the chezmoi repository,
    accounts for the direction of the operation to color the diff."""

    # not focussable https://textual.textualize.io/widgets/static/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    diff_spec: reactive[tuple[Path, str] | None] = reactive(None, init=False)

    # override property from ScrollableContainer to allow maximizing
    @property
    def allow_maximize(self) -> bool:
        return True

    def on_mount(self) -> None:
        text = "Click a file or directory, \nto show the diff."
        self.update(Text(text, style="dim"))

    def watch_diff_spec(self) -> None:
        if self.diff_spec is None:
            self.update("Click a file to see its diff")
        assert self.diff_spec is not None and isinstance(self.diff_spec, tuple)

        diff_output: list[str]
        if self.diff_spec[1] == "apply":
            if self.diff_spec[0] not in chezmoi.status_paths["apply_files"]:
                self.update(
                    Content("\n").join(
                        [
                            f"No diff available for {self.diff_spec[0]}",
                            "File not in chezmoi status output.",
                        ]
                    )
                )
                return
            else:
                diff_output = chezmoi.run.apply_diff(self.diff_spec[0])
        elif self.diff_spec[1] == "re-add":
            if self.diff_spec[0] not in chezmoi.status_paths["re_add_files"]:
                self.update(
                    Content("\n").join(
                        [
                            f"No diff available for {self.diff_spec[0]}",
                            "File not in chezmoi status output.",
                        ]
                    )
                )
                return
            else:
                diff_output = chezmoi.run.re_add_diff(self.diff_spec[0])

        if not diff_output:
            self.update(
                Content(
                    f"chezmoi diff {self.diff_spec[0]} returned no output."
                )
            )
            return

        diff_lines: list[str] = [
            line
            for line in diff_output
            if line.strip()  # filter lines containing only spaces
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        ]

        if diff_output:
            max_len = max(len(line) for line in diff_output)
        else:
            max_len = 0
        padded_lines = [line.ljust(max_len) for line in diff_lines]
        colored_lines: list[Content] = []
        for line in padded_lines:
            if line.startswith("-"):
                colored_lines.append(Content(line).stylize("$text-error"))
            elif line.startswith("+"):
                colored_lines.append(Content(line).stylize("$text-success"))
            else:
                content = Content("\u2022" + line)  # bullet •
                colored_lines.append(content.stylize("dim"))
        self.update(Content("\n").join(colored_lines))


@dataclass
class NodeData:
    path: Path
    found: bool
    is_file: bool
    status: str


class ManagedTree(Tree[NodeData]):
    """Shows the tree widget on the left for Apply and Re-Add tabs."""

    unchanged: reactive[bool] = reactive(False, init=False)
    direction: reactive[Literal["apply", "re_add"]] = reactive("apply")
    flat_list: reactive[bool] = reactive(False, init=False)

    # TODO: default color should be updated on theme change
    node_colors = {
        "Dir": "#57A5E2",  # text-primary
        "D": "#D17E92",  # text-error
        "A": "#8AD4A1",  # text-success
        "M": "#FFC473",  # text-warning
    }

    # def __init__(self, **kwargs) -> None:
    # self.direction: Literal["apply", "re_add"] = direction
    # self.flat_list: bool = flat_list
    # super().__init__(label="root", **kwargs)

    @property
    def status_dirs(self):
        if self.direction == "apply":
            return chezmoi.status_paths["apply_dirs"]
        elif self.direction == "re_add":
            return chezmoi.status_paths["re_add_dirs"]
        else:
            return {}

    @property
    def status_files(self):
        if self.direction == "apply":
            return chezmoi.status_paths["apply_files"]
        elif self.direction == "re_add":
            return chezmoi.status_paths["re_add_files"]
        else:
            return {}

    def on_mount(self) -> None:

        self.guide_depth = 3
        # give root node status R so it's not considered having status "X"
        if self.root.data is None:
            self.root.data = NodeData(
                path=chezmoi.dest_dir, found=True, is_file=False, status="R"
            )
        self.show_root = False
        if not self.flat_list:
            self.add_nodes(self.root)
            self.add_leaves(self.root)
        elif self.flat_list:
            self.add_flat_leaves()

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
        if not self.unchanged:
            return any(f in self.status_files for f in managed_in_dir_tree)

        # include_unchanged_files=False
        elif self.unchanged:
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
        if not self.unchanged:
            return node_data.status != "X"
        # include_unchanged_files=True
        return True

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

        status_code = "X"
        assert isinstance(tree_node.data, NodeData)
        # if not flat:
        file_paths = chezmoi.managed_file_paths_in_dir(tree_node.data.path)
        for file_path in file_paths:
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

    def add_flat_leaves(self) -> None:
        # include_unchanged_files=False
        for file_path in self.status_files:
            node_data = NodeData(
                path=file_path,
                found=file_path.exists(),
                is_file=True,
                status=self.status_files[file_path],
            )
            node_label = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

        # add additional leaves when include_unchanged_files=True
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
        event.stop()
        self.add_nodes(event.node)
        self.add_leaves(event.node)

    def watch_unchanged(self) -> None:
        """Update the visible nodes in the tree based on the current filter
        settings."""
        if not self.flat_list:

            def get_expanded_nodes() -> list[TreeNode]:
                """Recursively get all current expanded nodes in the tree."""

                current_node = self.root

                def collect_nodes(current_node: TreeNode) -> list[TreeNode]:
                    nodes = [current_node]
                    for child in current_node.children:
                        if child.is_expanded:
                            nodes.append(child)
                            nodes.extend(collect_nodes(child))
                    return nodes

                return collect_nodes(current_node)

            for node in get_expanded_nodes():
                self.add_nodes(node)
                self.add_leaves(node)

        elif self.flat_list:
            self.clear()
            self.add_flat_leaves()


class FilteredDirTree(DirectoryTree):
    """Provides a fast DirectoryTree to explore any path in the destination
    directory which can be added to the chezmoi repository.

    No mather how large the tree in the destination directory is and with the
    ability to filter the tree for easy access to paths to be considered adding
    to the chezmoi repository.
    """

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
