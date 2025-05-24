"""Contains classes used as reused components by the widgets in mousse.py."""

import os

from dataclasses import dataclass
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, HorizontalGroup, Vertical
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Label,
    RichLog,
    Static,
    Switch,
    Tree,
)
from textual.widgets.tree import TreeNode

from chezmoi_mousse.chezmoi import chezmoi


class GitLog(DataTable):

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, path: Path | None = None) -> None:
        super().__init__(id="git_log")
        self.path = path

    def on_mount(self) -> None:
        self.show_cursor = False
        if self.path is None:
            self.populate_data_table(chezmoi.git_log)

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
        self.populate_data_table(chezmoi.git_log_path(str(self.path)))


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


class PathView(Container):
    """RichLog widget to display the content of a file with highlighting."""

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    path: reactive[Path | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield RichLog(
            id="file_preview",
            classes="file-preview",
            auto_scroll=False,
            wrap=False,
            highlight=True,
        )

    def update_path_view(self, path: Path) -> None:
        assert isinstance(self.path, Path)
        rich_log = self.query_one("#file_preview", RichLog)
        truncated = ""
        try:
            if self.path.stat().st_size > 150 * 1024:
                truncated = (
                    "\n\n------ File content truncated to 150 KiB ------\n"
                )
        except PermissionError as error:
            rich_log.write(error.strerror)
            return
        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.path in chezmoi.managed_file_paths:
                file_content = chezmoi.cat(str(self.path))
                if not file_content.strip():
                    rich_log.write("File contains only whitespace")
                else:
                    rich_log.write(file_content)
                return

        if self.path in chezmoi.managed_dir_paths:
            text = [
                "The directory is managed, and does not exist on disk.",
                f'Output from "chezmoi status {self.path}"',
                f"{chezmoi.status(str(self.path))}",
            ]
            rich_log.write("\n".join(text))
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if not file_content.strip():
                    rich_log.write("File contains only whitespace")
                else:
                    rich_log.write(file_content + truncated)

        except IsADirectoryError:
            rich_log.write(f"Directory: {self.path}")
            return

        except UnicodeDecodeError:
            text = f"{self.path} cannot be decoded as UTF-8."
            rich_log.write(f"{self.path} cannot be decoded as UTF-8.")
            return

        except OSError as error:
            text = Content(f"Error reading {self.path}: {error}")
            rich_log.write(text)

    def watch_path(self) -> None:
        if self.path is not None:
            self.query_one(RichLog).clear()
            self.update_path_view(self.path)


class DiffView(Horizontal):

    BINDINGS = [Binding(key="M,m", action="maximize", description="maximize")]

    diff_spec: reactive[tuple[Path, str] | None] = reactive(None, init=False)

    # override property from ScrollableContainer to allow maximizing
    @property
    def allow_maximize(self) -> bool:
        return True

    def compose(self) -> ComposeResult:
        yield Static("Click a file to see its diff")

    def watch_diff_spec(self) -> None:
        assert self.diff_spec is not None and isinstance(self.diff_spec, tuple)
        static_diff = self.query_exactly_one(Static)

        diff_output: list[str]
        if self.diff_spec[1] == "apply":
            if self.diff_spec[0] not in chezmoi.status_paths["apply_files"]:
                static_diff.update(
                    Content("\n").join(
                        [
                            f"No diff available for {self.diff_spec[0]}",
                            "File not in chezmoi status output.",
                        ]
                    )
                )
                return
            else:
                diff_output = chezmoi.apply_diff(str(self.diff_spec[0]))
        elif self.diff_spec[1] == "re-add":
            if self.diff_spec[0] not in chezmoi.status_paths["re_add_files"]:
                static_diff.update(
                    Content("\n").join(
                        [
                            f"No diff available for {self.diff_spec[0]}",
                            "File not in chezmoi status output.",
                        ]
                    )
                )
                return
            else:
                diff_output = chezmoi.re_add_diff(str(self.diff_spec[0]))

        if not diff_output:
            static_diff.update(
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
        static_diff.update(Content("\n").join(colored_lines))


@dataclass
class NodeData:
    path: Path
    found: bool
    is_file: bool
    status: str


class ManagedTree(Vertical):

    unchanged: reactive[bool] = reactive(False, init=False)

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
        with Horizontal(id="tree_buttons_horizontal"):
            with Vertical(classes="tree-button-vertical"):
                yield Button("Tree", id="tree_button_tree")
            with Vertical(classes="tree-button-vertical"):
                yield Button("Status", id="tree_button_status")
        yield Tree(label="root", classes="managed-tree")

    def on_mount(self) -> None:
        tree_buttons = self.query_one("#tree_buttons_horizontal", Horizontal)
        tree_buttons.border_subtitle = f"{chezmoi.dest_dir}{os.sep}"

        tree = self.query_exactly_one(Tree)
        tree.guide_depth = 2
        if tree.root.data is None:
            tree.root.data = NodeData(
                path=chezmoi.dest_dir, found=True, is_file=False, status="R"
            )
        # give root node status R so it's not considered having status "X"
        tree.show_root = False
        self.add_nodes(tree.root)
        self.add_leaves(tree.root)

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
        event.stop()
        if not isinstance(event.node.data, NodeData):
            return
        self.add_nodes(event.node)
        self.add_leaves(event.node)

    def watch_unchanged(self) -> None:
        """Update the visible nodes in the tree based on the current filter
        settings."""
        root_node = self.query_exactly_one(Tree).root
        expanded_nodes = self.get_expanded_nodes(root_node)
        for node in expanded_nodes:
            self.add_nodes(node)
            self.add_leaves(node)


class FilterSwitch(HorizontalGroup):
    """A switch, a label and a tooltip."""

    def __init__(self, switch_data: dict[str, str], switch_id: str) -> None:
        super().__init__(classes="filter-container")
        self.switch_data = switch_data
        self.switch_id = switch_id

    def compose(self) -> ComposeResult:
        yield Switch(id=self.switch_id, classes="filter-switch")
        yield Label(
            self.switch_data["label"], classes="filter-label"
        ).with_tooltip(tooltip=self.switch_data["tooltip"])
