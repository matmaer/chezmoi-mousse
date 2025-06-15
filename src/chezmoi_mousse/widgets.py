"""Contains classes used as widgets by the main_tabs.py module.

These classes
- inherit directly from built in textual widgets
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't call any query methods
- don't apply tcss classes
- don't import from main_tabs.py, gui.py or containers.py modules
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
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    DirectoryTree,
    RichLog,
    Static,
    Tree,
)
from textual.widgets.tree import TreeNode

import chezmoi_mousse.theme as theme
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import chars, unwanted
from chezmoi_mousse.type_definitions import (
    Area,
    ButtonLabel,
    ComponentName,
    FilterName,
    TabName,
)


class TabIdMixin:
    def __init__(self, tab: TabName) -> None:
        self.tab_name: TabName = tab
        self.tab_main_horizontal_id = f"{self.tab_name}_main_horizontal"
        self.filter_slider_id = f"{self.tab_name}_filter_slider"
        self.tree_tab_switchers_id = f"{self.tab_name}_tree_tab_switchers"

    def button_id(self, button_label: ButtonLabel) -> str:
        # replace spaces with underscores to make it a valid id
        button_id = button_label.replace(" ", "_")
        return f"{self.tab_name}_{button_id}_button"

    def buttons_horizontal_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_buttons_horizontal"

    def button_vertical_id(self, button_label: ButtonLabel) -> str:
        """Generate an id for each button in a vertical container to center
        them by applying auto width and align on this container."""
        button_id = button_label.replace(" ", "_")
        return f"{self.tab_name}_{button_id}_button_vertical"

    def component_id(self, component_name: ComponentName) -> str:
        """Generate an id for items imported from components.py."""
        return f"{self.tab_name}_{component_name}_component"

    def content_switcher_id(self, area: Area) -> str:
        return f"{self.tab_name}_{area}_content_switcher"

    def filter_horizontal_id(self, filter_name: FilterName) -> str:
        return f"{self.tab_name}_{filter_name}_filter_horizontal"

    def filter_label_id(self, filter_name: FilterName) -> str:
        return f"{self.tab_name}_{filter_name}_filter_label"

    def filter_item_id(self, filter_name: FilterName) -> str:
        return f"{self.tab_name}_{filter_name}_filter_switch"

    def tab_vertical_id(self, area: Area) -> str:
        """Generate an id for the main left and right vertical containers in a
        tab."""
        return f"{self.tab_name}_{area}_vertical"


class CheckBox(Checkbox, TabIdMixin):
    """Checkbox widget to be used in the filter sliders."""

    BUTTON_INNER = chars.check_mark

    def __init__(
        self, tab: TabName, *, filter_name: FilterName, **kwargs
    ) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(
            id=self.filter_item_id(filter_name), label="", **kwargs
        )

    def on_mount(self) -> None:
        self.compact = True


class TabButton(Button, TabIdMixin):

    def __init__(self, tab, *, button_label: ButtonLabel, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(
            label=button_label, id=self.button_id(button_label), **kwargs
        )

    def on_mount(self) -> None:
        self.active_effect_duration = 0
        self.compact = True


class GitLog(DataTable, TabIdMixin):
    """DataTable widget to display the output of the `git log` command, either
    for a specific path or the chezmoi repository as a whole.

    Does not call the git command directly, calls it through chezmoi.
    """

    # focussable  https://textual.textualize.io/widgets/data_table/

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab: TabName, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(id=self.component_id("GitLog"), **kwargs)

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


class PathView(RichLog, TabIdMixin):
    # focussable https://textual.textualize.io/widgets/rich_log/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab: TabName, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(
            id=self.component_id("PathView"),
            auto_scroll=True,
            wrap=True,
            highlight=True,
            **kwargs,
        )

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

        except OSError as error:
            text = Text(f"Error reading {self.path}: {error}")
            self.write(text)

    def watch_path(self) -> None:
        if self.path is not None:
            self.clear()
            self.update_path_view()


class DiffView(RichLog, TabIdMixin):
    # not focussable https://textual.textualize.io/widgets/static/

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, tab: TabName, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(id=self.component_id("DiffView"), **kwargs)

    def on_mount(self) -> None:
        self.write(
            Text("Click a file  with status to show the diff.", style="dim")
        )

    def watch_path(self) -> None:
        self.clear()

        diff_output: list[str]
        status_files = chezmoi.status_paths[self.tab_name].files

        if self.path not in status_files:
            self.write(
                Text(
                    f"No diff available for {self.path}, file not present in chezmoi status output.",
                    style="dim",
                )
            )
            return

        if self.tab_name == "Apply":
            diff_output = chezmoi.run.apply_diff(self.path)
        elif self.tab_name == "Re-Add":
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
                self.write(Text(chars.bullet + line, style="dim"))


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

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab: TabName, **kwargs) -> None:
        self.tab_name: TabName = tab
        self.node_colors = {
            "Dir": theme.vars["text-primary"],
            "D": theme.vars["text-error"],
            "A": theme.vars["text-success"],
            "M": theme.vars["text-warning"],
        }
        root_node_data = DirNodeData(
            path=chezmoi.dest_dir, found=True, status="M"
        )
        super().__init__(label="root", data=root_node_data, **kwargs)

    def on_mount(self) -> None:
        self.guide_depth = 3
        self.show_root = False

    def should_show_node(self, node_data: NodeData) -> bool:
        if isinstance(node_data, FileNodeData):
            if not self.unchanged:
                return node_data.status != "X"
            return True
        elif isinstance(node_data, DirNodeData):
            if node_data.path == chezmoi.dest_dir:
                return True
            managed_files_in_sub_dir = [
                f
                for f in chezmoi.managed_file_paths
                if node_data.path in f.parents
            ]
            managed_dirs_in_sub_dir = [
                f
                for f in chezmoi.managed_dir_paths
                if node_data.path in f.parents
                or node_data.path.parent == chezmoi.dest_dir
            ]
            status_files = chezmoi.status_paths[self.tab_name].files
            if not self.unchanged:
                return any(f in status_files for f in managed_files_in_sub_dir)
            else:
                return (
                    bool(managed_dirs_in_sub_dir)
                    or bool(managed_files_in_sub_dir)
                    and node_data.path in chezmoi.managed_dir_paths
                )
        return False

    def add_leaves(self, tree_node: TreeNode) -> None:
        current_leafs = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, FileNodeData)
        ]
        for leaf in current_leafs:
            leaf.remove()

        status_code = "X"
        assert isinstance(tree_node.data, DirNodeData)
        file_paths = chezmoi.managed_file_paths_in_dir(tree_node.data.path)
        status_files = chezmoi.status_paths[self.tab_name].files
        for file_path in file_paths:
            if file_path in status_files:
                status_code = status_files[file_path]
            node_data = FileNodeData(
                path=file_path, found=file_path.exists(), status=status_code
            )
            if self.should_show_node(node_data):
                node_label = self.style_label(node_data)
                tree_node.add_leaf(label=node_label, data=node_data)

    def add_nodes(self, tree_node: TreeNode) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        dir_paths = chezmoi.managed_dir_paths_in_dir(tree_node.data.path)
        status_dirs = chezmoi.status_paths[self.tab_name].dirs

        # Remove directory nodes that no longer match the filter
        for child in list(tree_node.children):
            if isinstance(
                child.data, DirNodeData
            ) and not self.should_show_node(child.data):
                child.remove()

        # Add directory nodes that now match the filter
        for dir_path in dir_paths:
            status_code = "X"
            if dir_path in status_dirs:
                status_code = status_dirs[dir_path]
            node_data = DirNodeData(
                path=dir_path, found=dir_path.exists(), status=status_code
            )
            # Only add if not already present and should be shown
            if self.should_show_node(node_data) and dir_path not in [
                child.data.path
                for child in tree_node.children
                if isinstance(child.data, DirNodeData)
            ]:
                node_label = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

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


class ManagedTree(TreeBase, TabIdMixin):

    def __init__(self, tab: TabName, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(tab, id=self.component_id("ManagedTree"), **kwargs)

    def on_mount(self) -> None:
        self.add_nodes(self.root)
        self.add_leaves(self.root)

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

    def watch_unchanged(self) -> None:
        """Update the visible nodes based on the "show unchanged" filter."""
        for node in self.get_expanded_nodes():
            self.add_nodes(node)
            self.add_leaves(node)


class ExpandedTree(TreeBase, TabIdMixin):
    def __init__(self, tab: TabName, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(tab, id=self.component_id("ExpandedTree"), **kwargs)

    def on_mount(self) -> None:
        self.expand_all_nodes(self.root)

    def expand_all_nodes(self, node: TreeNode) -> None:
        """Recursively expand all directory nodes."""
        if (
            node.data
            and isinstance(node.data, DirNodeData)
            and self.should_show_node(node.data)
        ):
            if not node.is_expanded:
                node.expand()
                self.add_nodes(node)
                self.add_leaves(node)
            for child in node.children:
                if child.data and isinstance(child.data, DirNodeData):
                    self.expand_all_nodes(child)


class FlatTree(TreeBase, TabIdMixin):
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab: TabName, **kwargs) -> None:
        TabIdMixin.__init__(self, tab)
        super().__init__(tab, id=self.component_id("FlatTree"), **kwargs)

    def on_mount(self) -> None:
        self.add_flat_leaves()

    def add_flat_leaves(self) -> None:
        status_files = chezmoi.status_paths[self.tab_name].files
        for file_path in status_files:
            node_data = FileNodeData(
                path=file_path,
                found=file_path.exists(),
                status=status_files[file_path],
            )
            node_label = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

    def watch_unchanged(self) -> None:
        for file_path in chezmoi.managed_file_paths_without_status:
            node_data = FileNodeData(
                path=file_path, found=file_path.exists(), status="X"
            )
            node_label = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)


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
            extension = re.match(r"\.[^.]*$", path.name)
            if extension in unwanted["files"]:
                return True
        return False
