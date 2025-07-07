"""Contains classes used as widgets by the main_tabs.py module.

These classes
- inherit directly from built in textual widgets
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't call any query methods
- don't apply tcss classes
- don't import from main_tabs.py, gui.py or containers.py modules
- don't have key bindings
"""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual.content import Content
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import DataTable, DirectoryTree, RichLog, Static
from textual.widgets.tree import TreeNode

import chezmoi_mousse.theme as theme
from chezmoi_mousse.chezmoi import chezmoi, cmd_log
from chezmoi_mousse.config import unwanted
from chezmoi_mousse.id_typing import (
    CharsEnum,
    IdMixin,
    NodeData,
    TabStr,
    TcssStr,
    TreeStr,
)
from chezmoi_mousse.overrides import CustomRenderLabel


class AutoWarning(Static):

    sign: str = CharsEnum.warning_sign.value

    def __init__(self, *, tab_str: TabStr, classes: str) -> None:
        super().__init__(classes=classes)
        self.tab_str = tab_str

    def on_mount(self) -> None:
        warning_lines: list[str] = []
        if self.tab_str in (TabStr.re_add_tab, TabStr.add_tab):
            if chezmoi.autocommit_enabled:
                warning_lines.append(
                    f"{self.sign}  Auto commit is enabled: files will also be committed  {self.sign}"
                )
            if chezmoi.autopush_enabled:
                warning_lines.append(
                    f"{self.sign}  Auto push is enabled: files will be pushed to the remote  {self.sign}"
                )
            warning_lines.append(
                f"{self.sign}  Dotfile manager will be updated with current local file  {self.sign}"
            )
        if self.tab_str == TabStr.apply_tab:
            warning_lines.append(
                f"{self.sign} Local file will be modified. {self.sign}"
            )

        # Apply text-warning markup to each line
        markup_lines = [
            Content.from_markup(f"[$text-warning]{line}[/]")
            for line in warning_lines
        ]
        self.update(Content("\n").join(markup_lines))


class OperateInfo(Static):

    bullet = CharsEnum.bullet.value

    def __init__(self, tab_str: TabStr, *, path: Path, classes: str) -> None:
        super().__init__(classes=classes)

        self.tab_str = tab_str
        self.path = path
        self.info_border_titles = {
            TabStr.apply_tab: CharsEnum.apply.value,
            TabStr.re_add_tab: CharsEnum.re_add.value,
            TabStr.add_tab: CharsEnum.add.value,
        }

    def on_mount(self) -> None:
        self.lines_to_write: list[str] = []

        if self.tab_str in (TabStr.apply_tab, TabStr.re_add_tab):
            self.lines_to_write.extend(
                [
                    "[$text-success]+ green lines will be added[/]",
                    "[$text-error]- red lines will be removed[/]",
                    f"[dim]{self.bullet} dimmed lines for context[/]",
                ]
            )
        else:
            self.lines_to_write.append(
                "[$text-success]Path will be added to your chezmoi dotfile manager.[/]"
            )
        self.update("\n".join(self.lines_to_write))
        self.border_title = str(self.path)
        self.border_subtitle = self.info_border_titles[self.tab_str]


class ContentsView(RichLog):

    path: reactive[Path | None] = reactive(None)

    def __init__(self, *, view_id: str) -> None:
        super().__init__(
            id=view_id, auto_scroll=False, wrap=True, highlight=True
        )

    def update_contents_view(self) -> None:
        assert isinstance(self.path, Path)
        truncated_message = ""
        cmd_log.log_read_file(self.path)
        try:
            if self.path.is_file() and self.path.stat().st_size > 150 * 1024:
                truncated_message = (
                    "\n\n------ File content truncated to 150 KiB ------\n"
                )
        except PermissionError as e:
            self.write(e.strerror)
            cmd_log.log_error("Permission denied")
            cmd_log.log_exception(f"{e}")
            return

        try:
            with open(self.path, "rt", encoding="utf-8") as file:
                file_content = file.read(150 * 1024)
                if not file_content.strip():
                    self.write("File contains only whitespace")
                    cmd_log.log_error(
                        "File is empty or contains only whitespace"
                    )
                else:
                    self.write(file_content + truncated_message)
                    cmd_log.log_output("Read file successful")

        except UnicodeDecodeError as e:
            self.write(f"{self.path} cannot be decoded as UTF-8.")
            cmd_log.log_error("File cannot be decoded as UTF-8")
            cmd_log.log_exception(f"{e}")
            return

        except FileNotFoundError:
            # FileNotFoundError is raised both when a file or a directory
            # does not exist
            if self.path in chezmoi.managed_file_paths:
                if not chezmoi.run.cat(self.path).strip():
                    message = "File contains only whitespace"
                    self.write(message)
                    cmd_log.log_error(message)
                else:
                    self.write(chezmoi.run.cat(self.path))
                return

        except IsADirectoryError:
            if self.path == chezmoi.dest_dir:
                text = "Click a file or directory, \nto show its contents.\n"
                self.write(Text(text, style="dim"))
                self.write("Current directory:")
                self.write(f"{chezmoi.dest_dir}")
                self.write(Text("(destDir)\n", style="dim"))
                self.write("Source directory:")
                self.write(f"{chezmoi.source_dir}")
                self.write(Text("(sourceDir)", style="dim"))
            elif self.path in chezmoi.managed_dir_paths:
                self.write(f"Managed directory: {self.path}")
            else:
                self.write(f"Unmanaged directory: {self.path}")
            cmd_log.log_output("Directory info displayed")

        except OSError as error:
            text = Text(f"Error reading {self.path}: {error}")
            self.write(text)
            cmd_log.log_error("Error reading file")
            cmd_log.log_exception(f"{error}")

    def watch_path(self) -> None:
        if self.path is None:
            self.path = chezmoi.dest_dir
        self.clear()
        self.update_contents_view()


class DiffView(RichLog):

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(
        self, *, tab_name: TabStr, view_id: str, classes: str = ""
    ) -> None:
        self.tab_name = tab_name
        super().__init__(
            id=view_id, auto_scroll=False, wrap=False, classes=classes
        )

    def on_mount(self) -> None:
        self.path = chezmoi.dest_dir

    def watch_path(self) -> None:
        self.clear()

        if self.path is None:
            self.path = chezmoi.dest_dir

        diff_output: list[str] = []
        status_files = chezmoi.managed_status[self.tab_name].files
        # create a diff view if the current path is a directory
        if (
            self.path in chezmoi.managed_status[self.tab_name].dirs
            or self.path == chezmoi.dest_dir
        ):
            status_files_in_dir = chezmoi.files_with_status_in(
                self.tab_name, self.path
            )
            if not status_files_in_dir:
                self.write(
                    Text(
                        "Directory does not contain changed files.",
                        style="dim",
                    )
                )
            else:
                self.write(Text("Files in directory with changed status:"))
                for file_path in status_files_in_dir:
                    self.write(Text(f"{file_path}"))
                    self.write(
                        Text(
                            "\nClick any file in the tree to see the diff.",
                            style="dim",
                        )
                    )
                return
            return
        # create a diff view if the current selected path is an unchanged file
        elif self.path not in status_files:
            self.write(
                Text(
                    f"No diff available for {self.path},\n file is unchanged.",
                    style="dim",
                )
            )
            return
        # create the actual diff view for a changed file
        if self.tab_name == TabStr.apply_tab:
            diff_output = chezmoi.run.apply_diff(self.path)
        elif self.tab_name == TabStr.re_add_tab:
            diff_output = chezmoi.run.re_add_diff(self.path)

        diff_lines: list[str] = [
            line
            for line in diff_output
            if line.strip()  # filter lines containing only spaces
            and line[0] in "+- "
            and not line.startswith(("+++", "---"))
        ]
        if not diff_lines:
            self.write(Text("No diff available."))
            return
        for line in diff_lines:
            line = line.rstrip("\n")
            if line.startswith("-"):
                self.write(Text(line, theme.vars["text-error"]))
            elif line.startswith("+"):
                self.write(Text(line, theme.vars["text-success"]))
            else:
                self.write(Text(CharsEnum.bullet.value + line, style="dim"))


class GitLogView(DataTable[Text]):
    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, view_id: str) -> None:
        super().__init__(id=view_id)

    def on_mount(self) -> None:
        self.show_cursor = False
        if self.path is None:
            self.path = chezmoi.dest_dir

    def add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
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
                self.add_row(*(Text(cell) for cell in columns))

    def watch_path(self) -> None:
        assert isinstance(self.path, Path)
        git_log_output = chezmoi.run.git_log(self.path)
        self.clear(columns=True)
        self.populate_data_table(git_log_output)


@dataclass
class DirNodeData(NodeData):
    pass


@dataclass
class FileNodeData(NodeData):
    pass


class TreeBase(CustomRenderLabel):  # instead of Tree[NodeData]

    def __init__(
        self,
        tab_str: TabStr,
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False
        self.tab_str: TabStr = tab_str
        self.node_colors: dict[str, str] = {
            "Dir": theme.vars["text-primary"],
            "D": theme.vars["text-error"],
            "A": theme.vars["text-success"],
            "M": theme.vars["text-warning"],
            # Root node, invisible but needed because render_label override
            "R": theme.vars["text-primary"],
        }
        root_node_data: DirNodeData = DirNodeData(
            path=chezmoi.dest_dir, found=True, status="R"
        )
        super().__init__(
            label="root", data=root_node_data, id=id, classes=classes
        )

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.show_root: bool = False

    # 4 methods to provide tab navigation without intaraction with the tree
    def on_key(self, event: Key) -> None:
        if event.key in ("tab", "shift+tab"):
            return
        self._initial_render = False
        self._user_interacted = True

    def on_click(self) -> None:
        self._initial_render = False
        self._user_interacted = True

    def on_focus(self) -> None:
        if self._first_focus:
            self._first_focus = False
            self.refresh()

    def on_blur(self) -> None:
        if not self._user_interacted and not self._first_focus:
            self._first_focus = True
            self.refresh()

    def create_dir_node_data(self, path: Path) -> DirNodeData:
        status_code: str = chezmoi.managed_status[self.tab_str].dirs[path]
        if not status_code:
            status_code = "X"
        found: bool = path.exists()
        return DirNodeData(path=path, found=found, status=status_code)

    def create_file_node_data(self, path: Path) -> FileNodeData:
        status_code: str = chezmoi.managed_status[self.tab_str].files[path]
        found: bool = path.exists()
        return FileNodeData(path=path, found=found, status=status_code)

    def get_expanded_nodes(self) -> list[TreeNode[NodeData]]:
        # Recursively calling collect_nodes
        nodes: list[TreeNode[NodeData]] = [self.root]

        def collect_nodes(
            current_node: TreeNode[NodeData],
        ) -> list[TreeNode[NodeData]]:
            expanded: list[TreeNode[NodeData]] = []
            for child in current_node.children:
                if child.is_expanded:
                    expanded.append(child)
                    expanded.extend(collect_nodes(child))
            return expanded

        nodes.extend(collect_nodes(self.root))
        return nodes

    def should_show_dir_node(self, dir_path: Path, unchanged: bool) -> bool:
        if not unchanged:
            has_status_files: bool = chezmoi.dir_has_status_files(
                self.tab_str, dir_path
            )
            has_status_dirs: bool = chezmoi.dir_has_status_dirs(
                self.tab_str, dir_path
            )
            return has_status_files or has_status_dirs
        return True

    def add_unchanged_leaves(self, tree_node: TreeNode[NodeData]) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        unchanged_in_dir: list[Path] = chezmoi.files_without_status_in(
            self.tab_str, tree_node.data.path
        )
        for file_path in unchanged_in_dir:
            node_data: FileNodeData = self.create_file_node_data(file_path)
            node_label: Text = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def remove_unchanged_leaves(self, tree_node: TreeNode[NodeData]) -> None:
        current_unchanged_leaves: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, FileNodeData) and leaf.data.status == "X"
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_leaves(self, tree_node: TreeNode[NodeData]) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        status_file_paths: list[Path] = chezmoi.files_with_status_in(
            self.tab_str, tree_node.data.path
        )
        for file in status_file_paths:
            node_data: FileNodeData = self.create_file_node_data(file)
            node_label: Text = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def add_dir_nodes(
        self, tree_node: TreeNode[NodeData], unchanged: bool
    ) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        for dir_path in chezmoi.managed_dirs_in(tree_node.data.path):
            if self.should_show_dir_node(dir_path, unchanged):
                node_data: DirNodeData = self.create_dir_node_data(dir_path)
                node_label: Text = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

    def remove_unchanged_dir_nodes(
        self, tree_node: TreeNode[NodeData], unchanged: bool
    ) -> None:
        assert isinstance(tree_node.data, DirNodeData)
        dir_nodes: list[TreeNode[NodeData]] = [
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
        italic: bool = False if node_data.found else True
        if node_data.status != "X":
            styled = Style(
                color=self.node_colors[node_data.status], italic=italic
            )
        elif isinstance(node_data, FileNodeData):
            styled = "dim"
        else:
            styled = self.node_colors["Dir"]
        return Text(node_data.path.name, style=styled)


class ManagedTree(TreeBase, IdMixin):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        super().__init__(
            tab_str,
            id=self.tree_id(TreeStr.managed_tree),
            classes=TcssStr.tree_widget,
        )

    def on_mount(self) -> None:
        self.add_dir_nodes(self.root, self.unchanged)
        self.add_status_leaves(self.root)

    def on_tree_node_expanded(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_dir_nodes(event.node, self.unchanged)
        self.add_status_leaves(event.node)
        if self.unchanged:
            self.add_unchanged_leaves(event.node)
        else:
            self.remove_unchanged_leaves(event.node)

    def on_tree_node_collapsed(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        event.node.remove_children()

    def watch_unchanged(self) -> None:
        for node in self.get_expanded_nodes():
            if self.unchanged:
                self.add_unchanged_leaves(node)
            if not self.unchanged:
                self.remove_unchanged_leaves(node)


class ExpandedTree(TreeBase, IdMixin):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        super().__init__(
            tab_str,
            id=self.tree_id(TreeStr.expanded_tree),
            classes=TcssStr.tree_widget,
        )

    def on_mount(self) -> None:
        self.expand_all_nodes(self.root)

    def expand_all_nodes(self, node: TreeNode[NodeData]) -> None:
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

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        super().__init__(
            tab_str,
            id=self.tree_id(TreeStr.flat_tree),
            classes=TcssStr.tree_widget,
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

    unmanaged_dirs: reactive[bool] = reactive(False)
    unwanted: reactive[bool] = reactive(False)

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
