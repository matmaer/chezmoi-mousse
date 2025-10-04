"""Contains classes used as widgets by the main_tabs.py module.

These classes
- inherit directly from built in textual widgets
- are not containers, but can be focussable or not
- don't override the parents' compose method
- don't call any query methods
- don't import from main_tabs.py, gui.py or containers.py modules
- don't have key bindings
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import DataTable, Link, ListItem, ListView, Static, Tree
from textual.widgets._tree import TOGGLE_STYLE
from textual.widgets.tree import TreeNode

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.chezmoi import ReadCmd
from chezmoi_mousse.id_typing import (
    AppType,
    Id,
    NodeData,
    PathDict,
    ScreenIds,
    TabIds,
)
from chezmoi_mousse.id_typing.enums import (
    Chars,
    OperateBtn,
    OperateHelp,
    TabName,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.messages import TreeNodeSelectedMsg


class OperateInfo(Static, AppType):

    def __init__(self, *, operate_btn: OperateBtn, path: Path) -> None:
        super().__init__(classes=Tcss.operate_info)

        self.operate_btn = operate_btn
        self.path = Path()

    def on_mount(self) -> None:
        self.border_title = str(self.path)
        lines_to_write: list[str] = []

        # show command help and set the subtitle
        if OperateBtn.apply_file == self.operate_btn:
            lines_to_write.append(OperateHelp.apply_file.value)
            self.border_subtitle = Chars.apply_file_info_border
        elif OperateBtn.re_add_file == self.operate_btn:
            lines_to_write.append(OperateHelp.re_add_file.value)
            self.border_subtitle = Chars.re_add_file_info_border
        elif OperateBtn.add_file == self.operate_btn:
            lines_to_write.append(OperateHelp.add.value)
            self.border_subtitle = Chars.add_file_info_border
        elif OperateBtn.forget_file == self.operate_btn:
            lines_to_write.append(OperateHelp.forget_file.value)
            self.border_subtitle = Chars.forget_file_info_border
        elif OperateBtn.destroy_file == self.operate_btn:
            lines_to_write.extend(OperateHelp.destroy_file.value)
            self.border_subtitle = Chars.destroy_file_info_border
        # show git auto warnings
        if not OperateBtn.apply_file == self.operate_btn:
            if self.app.git_autocommit:
                lines_to_write.append(OperateHelp.auto_commit.value)
            if self.app.git_autopush:
                lines_to_write.append(OperateHelp.autopush.value)
        # show git diff color info
        if (
            OperateBtn.apply_file == self.operate_btn
            or OperateBtn.re_add_file == self.operate_btn
        ):
            lines_to_write.extend(OperateHelp.diff_color.value)
        self.update("\n".join(lines_to_write))


class GitLogView(DataTable[Text], AppType):

    path: reactive[Path | None] = reactive(None, init=False)

    # TODO: implement footer binding to toggle text wrap in second column of the datatable

    def __init__(self, *, tab_ids: TabIds | ScreenIds) -> None:
        self.tab_ids = tab_ids
        self.row_styles = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
        }
        super().__init__(
            id=self.tab_ids.view_id(view=ViewName.git_log_view),
            show_cursor=False,
        )

    def add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        self.add_row(*row)

    def render_invalid_data(self, new_data: str):
        self.clear(columns=True)
        self.add_column(
            Text("INVALID DATA RECEIVED", self.row_styles["error"])
        )
        if new_data == "":
            self.add_row(Text("received an empty string"))
            return
        elif type(new_data) is str:
            self.add_row(
                Text("Received invalid string:", self.row_styles["warning"])
            )
            self.add_row(Text(new_data))

        elif type(new_data) is not str:
            self.add_row(Text(f"Received invalid data type: {type(new_data)}"))
            self.add_row(Text(str(new_data)))
            return
        else:
            raise ValueError("Unhandled invalid data in GitLogView")

    def populate_data_table(self, cmd_output: str) -> None:
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
        styles = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
        }
        for line in cmd_output.splitlines():
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
        if self.path is None:
            return
        if self.path == self.app.destDir:
            cmd_output = self.app.chezmoi.read(ReadCmd.git_log)
        else:
            source_path = Path(
                self.app.chezmoi.read(ReadCmd.source_path, self.path)
            )
            cmd_output = self.app.chezmoi.read(ReadCmd.git_log, source_path)
        try:
            self.populate_data_table(cmd_output)
        except:  # noqa: E722
            self.render_invalid_data(cmd_output)


class TreeBase(Tree[NodeData], AppType):

    def __init__(self, tab_ids: TabIds, *, tree_name: TreeName) -> None:
        self.tree_name = tree_name
        self.tab_ids = tab_ids
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False
        self.node_selected_msg = TreeNodeSelectedMsg()
        self.node_colors: dict[str, str] = {
            "Dir": theme.vars["text-primary"],
            "D": theme.vars["text-error"],
            "A": theme.vars["text-success"],
            "M": theme.vars["text-warning"],
            # Root node, invisible but needed because render_label override
            # Use "F" for fake, as R is in use by chezmoi for Run
            "F": theme.vars["text-primary"],
        }
        # Initialize with a placeholder path, will be set properly in on_mount
        root_node_data = NodeData(
            path=Path("."), is_dir=True, found=True, status="F"
        )
        super().__init__(
            label="root",
            data=root_node_data,
            id=self.tab_ids.tree_id(tree=self.tree_name),
        )

    def on_mount(self) -> None:
        self.guide_depth: int = 3
        self.show_root: bool = False
        self.add_class(Tcss.tree_widget)
        if self.root.data:
            self.root.data.path = self.app.destDir

    @on(Tree.NodeSelected)
    def send_node_context_message(
        self, event: Tree.NodeSelected[NodeData]
    ) -> None:
        if event.node == self.root:
            return
        if (
            event.node.parent is not None
            and event.node.parent.data is not None
            and event.node.data is not None
        ):
            self.node_selected_msg = TreeNodeSelectedMsg(
                tree_name=self.tree_name,
                node_data=event.node.data,
                node_parent=event.node.parent.data,
                node_leaves=[
                    child.data
                    for child in event.node.children
                    if child.data is not None and child.data.is_dir is False
                ],
                node_subdirs=[
                    child.data
                    for child in event.node.children
                    if child.data is not None and child.data.is_dir is True
                ],
            )
        else:
            return
        self.post_message(self.node_selected_msg)

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

    # the styling method for the node labels
    def style_label(self, node_data: NodeData) -> Text:
        italic: bool = False if node_data.found else True
        if node_data.status != "X":
            styled = Style(
                color=self.node_colors[node_data.status], italic=italic
            )
        elif not node_data.is_dir:
            styled = "dim"
        else:
            styled = self.node_colors["Dir"]
        return Text(node_data.path.name, style=styled)

    # create node data methods
    def create_dir_node_data(self, *, path: Path) -> NodeData:
        status_code: str = ""
        if self.tab_ids.tab_name == TabName.apply_tab.name:
            status_code: str = self.app.chezmoi.apply_dirs[path]
        elif self.tab_ids.tab_name == TabName.re_add_tab.name:
            status_code: str = self.app.chezmoi.re_add_dirs[path]
        if not status_code:
            status_code = "X"
        found: bool = path.exists()
        return NodeData(
            path=path, is_dir=True, found=found, status=status_code
        )

    def create_file_node_data(self, *, path: Path) -> NodeData:
        status_code: str = ""
        if self.tab_ids.tab_name == TabName.apply_tab.name:
            status_code: str = self.app.chezmoi.apply_files[path]
        elif self.tab_ids.tab_name == TabName.re_add_tab.name:
            status_code: str = self.app.chezmoi.re_add_files[path]
        if not status_code:
            status_code = "X"
        found: bool = path.exists()
        return NodeData(
            path=path, is_dir=False, found=found, status=status_code
        )

    # node visibility methods
    def dir_has_status_files(self, tab_name: str, dir_path: Path) -> bool:
        # checks for any, direct children or no matter how deep in subdirs
        files_dict: PathDict = {}
        if tab_name == TabName.apply_tab.name:
            files_dict = self.app.chezmoi.apply_files
        elif tab_name == TabName.re_add_tab.name:
            files_dict = self.app.chezmoi.re_add_files

        return any(
            f
            for f, status in files_dict.items()
            if dir_path in f.parents and status != "X"
        )

    def dir_has_status_dirs(self, tab_name: str, dir_path: Path) -> bool:
        # checks for any, direct children or no matter how deep in subdirs
        dirs_dict: PathDict = {}
        if tab_name == TabName.apply_tab.name:
            dirs_dict = self.app.chezmoi.apply_dirs
        elif tab_name == TabName.re_add_tab.name:
            dirs_dict = self.app.chezmoi.re_add_dirs
        if dir_path in dirs_dict and dirs_dict[dir_path] != "X":
            return True

        return any(
            f
            for f, status in dirs_dict.items()
            if dir_path in f.parents and status != "X"
        )

    def should_show_dir_node(
        self, *, dir_path: Path, show_unchanged: bool = False
    ) -> bool:
        if show_unchanged:
            return True
        has_status_files: bool = self.dir_has_status_files(
            self.tab_ids.tab_name, dir_path
        )
        has_status_dirs: bool = self.dir_has_status_dirs(
            self.tab_ids.tab_name, dir_path
        )
        return has_status_files or has_status_dirs

    # node add/remove methods
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

    def add_unchanged_leaves(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            return
        unchanged_in_dir: list[Path] = (
            self.app.chezmoi.files_without_status_in(
                self.tab_ids.tab_name, tree_node.data.path
            )
        )
        for file_path in unchanged_in_dir:
            node_data: NodeData = self.create_file_node_data(path=file_path)
            node_label: Text = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def remove_unchanged_leaves(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        current_unchanged_leaves: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if leaf.data is not None
            and leaf.data.is_dir is False
            and leaf.data.status == "X"
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_leaves(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            return
        status_file_paths: list[Path] = self.app.chezmoi.files_with_status_in(
            self.tab_ids.tab_name, tree_node.data.path
        )
        # get current visible leaves
        current_leaves: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if isinstance(leaf.data, NodeData)
        ]
        current_leaf_paths = [
            leaf.data.path for leaf in current_leaves if leaf.data
        ]
        for file in status_file_paths:
            node_data: NodeData = self.create_file_node_data(path=file)
            if node_data.path in current_leaf_paths:
                continue
            node_label: Text = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def add_dir_nodes(
        self, *, tree_node: TreeNode[NodeData], show_unchanged: bool = False
    ) -> None:
        if tree_node.data is None:
            return
        # get current visible leaves
        current_dirs: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if leaf.data and leaf.data.is_dir is True
        ]
        current_dir_paths = [
            dir_node.data.path for dir_node in current_dirs if dir_node.data
        ]
        for dir_path in self.app.chezmoi.managed_dirs_in(tree_node.data.path):
            if dir_path in current_dir_paths:
                continue
            if self.should_show_dir_node(
                dir_path=dir_path, show_unchanged=show_unchanged
            ):
                node_data: NodeData = self.create_dir_node_data(path=dir_path)
                node_label: Text = self.style_label(node_data)
                tree_node.add(label=node_label, data=node_data)

    def remove_unchanged_dir_nodes(
        self, *, tree_node: TreeNode[NodeData], show_unchanged: bool = False
    ) -> None:
        dir_nodes: list[TreeNode[NodeData]] = [
            dir_node
            for dir_node in tree_node.children
            if dir_node.data is not None
            and dir_node.data.is_dir is True
            and dir_node.data.status == "X"
        ]
        for dir_node in dir_nodes:
            if (
                dir_node.data is not None
                and not self.should_show_dir_node(
                    dir_path=dir_node.data.path, show_unchanged=show_unchanged
                )
                and dir_node.data.path != self.app.destDir
            ):
                dir_node.remove()

    def remove_node_path(self, *, node_path: Path) -> None:
        # find corresponding node for the given path
        parents_with_removeable_nodes: list[TreeNode[NodeData] | None] = []
        for node in self.get_expanded_nodes():
            if (
                node.data
                and node.data.path == node_path
                and node.data.path != self.app.destDir
            ):
                parents_with_removeable_nodes.append(node.parent)
                node.remove()
        # after removing the node, check if the parent dir node contains any leaves
        for parent in parents_with_removeable_nodes:
            if (
                parent is not None
                and parent.data is not None
                and parent.data.is_dir is True
            ):
                parent.remove()
        self.refresh()

    def _apply_cursor_style(self, node_label: Text, is_cursor: bool) -> Text:
        """Helper to apply cursor-specific styling to a node label."""
        if not is_cursor:
            return node_label

        current_style = node_label.style
        # Apply bold styling when tree is first focused
        if not self._first_focus and self._initial_render:
            if isinstance(current_style, str):
                cursor_style = Style.parse(current_style) + Style(bold=True)
            else:
                cursor_style = current_style + Style(bold=True)
            return Text(node_label.plain, style=cursor_style)
        # Apply underline styling only after actual user interaction
        elif self._user_interacted:
            if isinstance(current_style, str):
                cursor_style = Style.parse(current_style) + Style(
                    underline=True
                )
            else:
                cursor_style = current_style + Style(underline=True)
            return Text(node_label.plain, style=cursor_style)

        return node_label  # No changes if conditions not met

    def render_label(
        self,
        node: TreeNode[NodeData],
        base_style: Style,
        style: Style,  # needed for valid overriding
    ) -> Text:
        # Get base styling from style_label
        if node.data is None:
            return Text("Node data is None")
        node_label = self.style_label(node.data)

        # Apply cursor styling via helper
        node_label = self._apply_cursor_style(
            node_label, node is self.cursor_node
        )

        if node.allow_expand:
            prefix = (
                (
                    self.ICON_NODE_EXPANDED
                    if node.is_expanded
                    else self.ICON_NODE
                ),
                base_style + TOGGLE_STYLE,
            )
        else:
            prefix = ("", base_style)

        text = Text.assemble(prefix, node_label)
        return text


class ManagedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        super().__init__(self.tab_ids, tree_name=TreeName.managed_tree)

    def refresh_tree_data(self) -> None:
        """Refresh the tree with latest chezmoi data."""
        self.root.remove_children()
        self.add_dir_nodes(tree_node=self.root, show_unchanged=self.unchanged)
        self.add_status_leaves(tree_node=self.root)

    @on(TreeBase.NodeExpanded)
    def update_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_dir_nodes(tree_node=event.node, show_unchanged=self.unchanged)
        self.add_status_leaves(tree_node=event.node)
        if self.unchanged:
            self.add_unchanged_leaves(tree_node=event.node)
        else:
            self.remove_unchanged_leaves(tree_node=event.node)

    @on(TreeBase.NodeCollapsed)
    def remove_node_children(
        self, event: TreeBase.NodeCollapsed[NodeData]
    ) -> None:
        event.node.remove_children()

    def watch_unchanged(self) -> None:
        for node in self.get_expanded_nodes():
            if self.unchanged:
                self.add_unchanged_leaves(tree_node=node)
                self.add_dir_nodes(
                    tree_node=node, show_unchanged=self.unchanged
                )
            if not self.unchanged:
                self.remove_unchanged_leaves(tree_node=node)
                self.remove_unchanged_dir_nodes(
                    tree_node=node, show_unchanged=self.unchanged
                )


class ExpandedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        super().__init__(self.tab_ids, tree_name=TreeName.expanded_tree)

    def refresh_tree_data(self) -> None:
        """Refresh the tree with latest chezmoi data."""
        self.root.remove_children()
        self.expand_all_nodes(self.root)

    @on(TreeBase.NodeExpanded)
    def add_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        event.stop()
        self.add_dir_nodes(tree_node=event.node, show_unchanged=self.unchanged)
        self.add_status_leaves(tree_node=event.node)
        if self.unchanged:
            self.add_unchanged_leaves(tree_node=event.node)
        else:
            self.remove_unchanged_leaves(tree_node=event.node)

    def expand_all_nodes(self, node: TreeNode[NodeData]) -> None:
        """Recursively expand all directory nodes."""
        if node.data is not None and node.data.is_dir is True:
            node.expand()
            self.add_dir_nodes(tree_node=node, show_unchanged=self.unchanged)
            self.add_status_leaves(tree_node=node)
            for child in node.children:
                if child.data is not None and child.data.is_dir is True:
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        expanded_nodes = self.get_expanded_nodes()
        for tree_node in expanded_nodes:
            if self.unchanged:
                self.add_unchanged_leaves(tree_node=tree_node)
                self.add_dir_nodes(
                    tree_node=tree_node, show_unchanged=self.unchanged
                )
            if not self.unchanged:
                self.remove_unchanged_leaves(tree_node=tree_node)
                self.remove_unchanged_dir_nodes(
                    tree_node=tree_node, show_unchanged=self.unchanged
                )


class FlatTree(TreeBase, AppType):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        super().__init__(self.tab_ids, tree_name=TreeName.flat_tree)

    def refresh_tree_data(self) -> None:
        """Refresh the tree with latest chezmoi data."""
        self.root.remove_children()
        files_dict: PathDict = {}
        if self.tab_ids.tab_name == TabName.apply_tab.name:
            files_dict = self.app.chezmoi.apply_files
        elif self.tab_ids.tab_name == TabName.re_add_tab.name:
            files_dict = self.app.chezmoi.re_add_files
        for file_path, status in files_dict.items():
            if status != "X":
                node_data = self.create_file_node_data(path=file_path)
                node_label = self.style_label(node_data)
                self.root.add_leaf(label=node_label, data=node_data)

    def add_all_unchanged_files(self) -> None:
        files_dict: PathDict = {}
        if self.tab_ids.tab_name == TabName.apply_tab.name:
            files_dict = self.app.chezmoi.apply_files
        elif self.tab_ids.tab_name == TabName.re_add_tab.name:
            files_dict = self.app.chezmoi.re_add_files
        for file_path, status in files_dict.items():
            if status == "X":
                node_data = self.create_file_node_data(path=file_path)
                node_label = self.style_label(node_data)
                self.root.add_leaf(label=node_label, data=node_data)

    def remove_flat_leaves(self) -> None:
        self.remove_unchanged_leaves(tree_node=self.root)

    def watch_unchanged(self) -> None:
        if self.unchanged:
            self.add_all_unchanged_files()
        elif not self.unchanged:
            self.remove_flat_leaves()


class DoctorTable(DataTable[Text]):

    def __init__(self) -> None:
        self.dr_style = {
            "ok": theme.vars["text-success"],
            "info": theme.vars["foreground-darken-1"],
            "warning": theme.vars["text-warning"],
            "failed": theme.vars["text-error"],
            "error": theme.vars["text-error"],
        }
        self.pw_mgr_commands: list[str] = []
        super().__init__(
            id=Id.config.datatable_id,
            show_cursor=False,
            classes=Tcss.doctor_table,
        )

    def populate_doctor_data(self, doctor_data: list[str]) -> list[str]:

        if not self.columns:
            self.add_columns(*doctor_data[0].split())

        for line in doctor_data[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                self.pw_mgr_commands.append((row[1]))
                new_row = [
                    Text(cell_text, style=self.dr_style["info"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] in ["ok", "warning", "error", "failed"]:
                new_row = [
                    Text(cell_text, style=f"{self.dr_style[row[0]]}")
                    for cell_text in row
                ]
                self.add_row(*new_row)
            elif row[0] == "info" and row[2] == "not set":
                self.pw_mgr_commands.append((row[1]))
                new_row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                self.add_row(*new_row)
            else:
                row = [Text(cell_text) for cell_text in row]
                self.add_row(*row)
        return self.pw_mgr_commands


class DoctorListView(ListView):

    class PwMgrInfo(Enum):
        @dataclass
        class PwMgrData:
            doctor_check: str
            description: str
            link: str

        age_command = PwMgrData(
            doctor_check="age-command",
            description="A simple, modern and secure file encryption tool",
            link="https://github.com/FiloSottile/age",
        )
        bitwarden_command = PwMgrData(
            doctor_check="bitwarden-command",
            description="Bitwarden Password Manager",
            link="https://github.com/bitwarden/cli",
        )
        bitwarden_secrets_command = PwMgrData(
            doctor_check="bitwarden-secrets-command",
            description="Bitwarden Secrets Manager CLI for managing secrets securely.",
            link="https://github.com/bitwarden/bitwarden-secrets",
        )
        doppler_command = PwMgrData(
            doctor_check="doppler-command",
            description="The Doppler CLI for managing secrets, configs, and environment variables.",
            link="https://github.com/DopplerHQ/cli",
        )
        gopass_command = PwMgrData(
            doctor_check="gopass-command",
            description="The slightly more awesome standard unix password manager for teams.",
            link="https://github.com/gopasspw/gopass",
        )
        keeper_command = PwMgrData(
            doctor_check="keeper-command",
            description="An interface to Keeper® Password Manager",
            link="https://github.com/Keeper-Security/Commander",
        )
        keepassxc_command = PwMgrData(
            doctor_check="keepassxc-command",
            description="Cross-platform community-driven port of Keepass password manager",
            link="https://keepassxc.org/",
        )
        lpass_command = PwMgrData(
            doctor_check="lpass-command",
            description="Old LastPass CLI for accessing your LastPass vault.",
            link="https://github.com/lastpass/lastpass-cli",
        )
        pass_command = PwMgrData(
            doctor_check="pass-command",
            description="Stores, retrieves, generates, and synchronizes passwords securely",
            link="https://www.passwordstore.org/",
        )
        pinentry_command = PwMgrData(
            doctor_check="pinentry-command",
            description="Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
            link="https://gnupg.org/related_software/pinentry/",
        )
        rbw_command = PwMgrData(
            doctor_check="rbw-command",
            description="Unofficial Bitwarden CLI",
            link="https://git.tozt.net/rbw",
        )
        vault_command = PwMgrData(
            doctor_check="vault-command",
            description="A tool for managing secrets",
            link="https://vaultproject.io/",
        )

    def __init__(self) -> None:
        super().__init__(
            id=Id.config.listview_id, classes=Tcss.doctor_listview
        )

    def populate_listview(self, pw_mgr_commands: list[str]) -> None:
        for cmd in pw_mgr_commands:
            for pw_mgr in DoctorListView.PwMgrInfo:
                if pw_mgr.value.doctor_check == cmd:
                    self.append(
                        ListItem(
                            Link(cmd, url=pw_mgr.value.link),
                            Static(pw_mgr.value.description),
                        )
                    )
                    break
