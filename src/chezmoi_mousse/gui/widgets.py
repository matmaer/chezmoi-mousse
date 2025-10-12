"""Contains classes which inherit from textual widgets."""

# RULES: These classes
# - inherit directly from built in textual widgets
# - are not containers, but can be focussable or not
# - don't override the parents' compose method
# - don't call any query methods
# - don't import from main_tabs.py, gui.py or containers.py modules
# - don't have key bindings
# - don't access any self.app in their __init__ method
# - don't access self.app attributes in their on_mount method which are updated after the loading screen completes in the App class on_mount method
# don't init any textual classes in the __init__  or on_mount method

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import DataTable, Link, ListItem, ListView, Static, Tree
from textual.widgets._tree import TOGGLE_STYLE
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    ActiveCanvas,
    Canvas,
    CanvasIds,
    Chars,
    Id,
    OperateBtn,
    PaneBtn,
    ReadCmd,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.gui import AppType, NodeData
from chezmoi_mousse.gui.messages import TreeNodeSelectedMsg

__all__ = [
    "GitLogView",
    "ManagedTree",
    "ExpandedTree",
    "FlatTree",
    "OperateInfo",
]


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    class Strings(StrEnum):
        container_id = "operate_help"
        add_file = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
        apply_file = "[$text-primary]The file in the destination directory will be modified.[/]"
        # apply_dir = "[$text-primary]The directory in the destination directory will be modified.[/]"
        auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
        autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
        destroy_file = "[$text-error]Permanently remove the file both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
        # destroy_dir = "[$text-error]Permanently remove the directory both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
        diff_color = "[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
        forget_file = "[$text-primary]Remove the file from the source state, i.e. stop managing them.[/]"
        # forget_dir = "[$text-primary]Remove the directory from the source state, i.e. stop managing them.[/]"
        re_add_file = "[$text-primary]Overwrite the source state with current local file[/]"
        # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"

    def __init__(self, *, operate_btn: OperateBtn) -> None:
        self.operate_btn = operate_btn
        super().__init__(
            id=OperateInfo.Strings.container_id, classes=Tcss.operate_info.name
        )

    def on_mount(self) -> None:
        lines_to_write: list[str] = []

        # show command help and set the subtitle
        if OperateBtn.apply_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.apply_file.value)
            self.border_subtitle = Chars.apply_file_info_border
        elif OperateBtn.re_add_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.re_add_file.value)
            self.border_subtitle = Chars.re_add_file_info_border
        elif OperateBtn.add_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.add_file.value)
            self.border_subtitle = Chars.add_file_info_border
        elif OperateBtn.forget_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.forget_file.value)
            self.border_subtitle = Chars.forget_file_info_border
        elif OperateBtn.destroy_file == self.operate_btn:
            lines_to_write.extend(OperateInfo.Strings.destroy_file.value)
            self.border_subtitle = Chars.destroy_file_info_border
        # show git auto warnings
        if not OperateBtn.apply_file == self.operate_btn:
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(OperateInfo.Strings.auto_commit.value)
            if self.git_autopush is True:
                lines_to_write.append(OperateInfo.Strings.autopush.value)
        # show git diff color info
        if (
            OperateBtn.apply_file == self.operate_btn
            or OperateBtn.re_add_file == self.operate_btn
        ):
            lines_to_write.extend(OperateInfo.Strings.diff_color.value)
        self.update("\n".join(lines_to_write))


class GitLogView(DataTable[Text], AppType):

    path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, *, canvas_ids: CanvasIds) -> None:
        self.canvas_ids = canvas_ids
        self.destDir: Path | None = None
        super().__init__(
            id=self.canvas_ids.view_id(view=ViewName.git_log_view),
            show_cursor=False,
            classes=Tcss.border_title_top.name,
        )

    def _add_row_with_style(self, columns: list[str], style: str) -> None:
        row: Iterable[Text] = [
            Text(cell_text, style=style) for cell_text in columns
        ]
        self.add_row(*row)

    def populate_data_table(self, cmd_output: str) -> None:
        self.clear(columns=True)
        self.add_columns("COMMIT", "MESSAGE")
        styles = {
            "ok": self.app.theme_variables["text-success"],
            "warning": self.app.theme_variables["text-warning"],
            "error": self.app.theme_variables["text-error"],
        }
        for line in cmd_output.splitlines():
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                self._add_row_with_style(columns, styles["ok"])
            elif columns[1].split(maxsplit=1)[0] == "Update":
                self._add_row_with_style(columns, styles["warning"])
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                self._add_row_with_style(columns, styles["error"])
            else:
                self.add_row(*(Text(cell) for cell in columns))

    def watch_path(self) -> None:
        if self.path is None:
            return
        self.border_title = f" {self.path} "
        if self.path == self.destDir:
            cmd_output = self.app.chezmoi.read(ReadCmd.git_log)
        else:
            source_path = Path(
                self.app.chezmoi.read(ReadCmd.source_path, self.path)
            )
            cmd_output = self.app.chezmoi.read(ReadCmd.git_log, source_path)
        self.populate_data_table(cmd_output)


class TreeBase(Tree[NodeData], AppType):

    def __init__(self, canvas_ids: CanvasIds, *, tree_name: TreeName) -> None:
        self.tree_name = tree_name
        self.canvas_ids = canvas_ids
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False
        if self.canvas_ids.canvas_name == Canvas.apply:
            self.active_canvas: ActiveCanvas = Canvas.apply
        else:
            self.active_canvas: ActiveCanvas = Canvas.re_add
        super().__init__(
            label="root",
            id=self.canvas_ids.tree_id(tree=self.tree_name),
            classes=Tcss.tree_widget.name,
        )

    def on_mount(self) -> None:
        self.node_colors: dict[str, str] = {
            "Dir": self.app.theme_variables["text-primary"],
            "D": self.app.theme_variables["text-error"],
            "A": self.app.theme_variables["text-success"],
            "M": self.app.theme_variables["text-warning"],
            " ": self.app.theme_variables["text-secondary"],
        }
        self.guide_depth: int = 3
        self.show_root: bool = False

    # the styling method for the node labels
    def style_label(self, node_data: NodeData) -> Text:
        italic: bool = False if node_data.found else True
        styled = "white"  # Default style
        if node_data.is_leaf:
            if node_data.status == "X":
                styled = "dim"
            elif node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == " ":
                styled = "white"
        elif not node_data.is_leaf:
            if node_data.status in "ADM":
                styled = Style(
                    color=self.node_colors[node_data.status], italic=italic
                )
            elif node_data.status == "X" or node_data.status == " ":
                styled = Style(color=self.node_colors[" "], italic=italic)
            else:
                styled = Style(color=self.node_colors["Dir"], italic=italic)

        return Text(node_data.path.name, style=styled)

    # create node data methods
    def create_node_data(
        self, *, path: Path, is_leaf: bool, status_code: str
    ) -> NodeData:
        found: bool = path.exists()
        return NodeData(
            path=path, is_leaf=is_leaf, found=found, status=status_code
        )

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

    def remove_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        current_unchanged_leaves: list[TreeNode[NodeData]] = [
            leaf
            for leaf in tree_node.children
            if leaf.data is not None
            and leaf.data.is_leaf is True
            and leaf.data.status == "X"
        ]
        for leaf in current_unchanged_leaves:
            leaf.remove()

    def add_status_files_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        # get current visible leaves
        current_leaves_with_status: list[Path] = [
            leaf.data.path
            for leaf in tree_node.children
            if leaf.data is not None
            and leaf.data.is_leaf is True
            and leaf.data.status == "X"
        ]
        if tree_node.data is None:
            return

        if self.tree_name == TreeName.flat_tree:
            status_files = self.app.chezmoi.all_status_files(
                self.active_canvas
            )
        else:
            status_files = self.app.chezmoi.status_files_in(
                self.active_canvas, tree_node.data.path
            )

        if self.active_canvas == PaneBtn.re_add_tab:
            # don't create nodes for non-existing files
            for file_path in status_files.copy():
                if not file_path.exists():
                    del status_files[file_path]

        for file_path, status_code in status_files.items():
            if file_path in current_leaves_with_status:
                continue
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code=status_code
            )
            node_label: Text = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def add_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        current_leaves_without_status: list[Path] = [
            leaf.data.path
            for leaf in tree_node.children
            if leaf.data is not None
            and leaf.data.is_leaf is True
            and leaf.data.status != "X"
        ]
        if tree_node.data is None:
            return

        files_without_status = self.app.chezmoi.files_without_status_in(
            self.active_canvas, tree_node.data.path
        )

        if self.active_canvas == PaneBtn.re_add_tab:
            # don't create nodes for non-existing files
            for file_path in files_without_status.copy():
                if not file_path.exists():
                    del files_without_status[file_path]

        for file_path, status_code in files_without_status.items():
            if file_path in current_leaves_without_status:
                continue
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code=status_code
            )
            node_label: Text = self.style_label(node_data)
            tree_node.add_leaf(label=node_label, data=node_data)

    def add_status_dirs_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        # get current visible dir nodes
        current_status_dirs: list[Path] = [
            dir_node.data.path
            for dir_node in tree_node.children
            if dir_node.data is not None
            and dir_node.data.is_leaf is False
            and dir_node.data.status == "X"
        ]
        if tree_node.data is None:
            return
        dir_paths = self.app.chezmoi.status_dirs_in(
            self.active_canvas, tree_node.data.path
        )
        for dir_path, status_code in dir_paths.items():
            if dir_path in current_status_dirs:
                continue
            node_data: NodeData = self.create_node_data(
                path=dir_path, is_leaf=False, status_code=status_code
            )
            node_label: Text = self.style_label(node_data)
            tree_node.add(label=node_label, data=node_data)

    def add_dirs_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            return
        # get current visible dir nodes
        current_dirs_without_status: list[Path] = [
            dir_node.data.path
            for dir_node in tree_node.children
            if dir_node.data is not None
            and dir_node.data.is_leaf is False
            and dir_node.data.status != "X"
        ]
        dir_paths = self.app.chezmoi.dirs_without_status_in(
            self.active_canvas, tree_node.data.path
        )
        for dir_path, status_code in dir_paths.items():
            if dir_path in current_dirs_without_status:
                continue
            node_data: NodeData = self.create_node_data(
                path=dir_path, is_leaf=False, status_code=status_code
            )
            node_label: Text = self.style_label(node_data)
            tree_node.add(label=node_label, data=node_data)

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

    @on(Tree.NodeCollapsed)
    def remove_node_children(
        self, event: Tree.NodeCollapsed[NodeData]
    ) -> None:
        event.node.remove_children()

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
                    if child.data is not None and child.data.is_leaf is True
                ],
                node_subdirs=[
                    child.data
                    for child in event.node.children
                    if child.data is not None and child.data.is_leaf is False
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


class ManagedTree(TreeBase):

    destDir: reactive[Path | None] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, canvas_ids: CanvasIds) -> None:
        self.canvas_ids = canvas_ids
        super().__init__(self.canvas_ids, tree_name=TreeName.managed_tree)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )

        self.add_status_dirs_in(tree_node=self.root)
        self.add_status_files_in(tree_node=self.root)

    @on(TreeBase.NodeExpanded)
    def update_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(tree_node=event.node)

    def watch_unchanged(self) -> None:
        for node in self.get_expanded_nodes():
            if self.unchanged:
                self.add_files_without_status_in(tree_node=node)
            else:
                self.remove_files_without_status_in(tree_node=node)


class ExpandedTree(TreeBase):

    destDir: reactive[Path | None] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, canvas_ids: CanvasIds) -> None:
        self.canvas_ids = canvas_ids
        super().__init__(self.canvas_ids, tree_name=TreeName.expanded_tree)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )
        self.expand_all_nodes(self.root)

    @on(TreeBase.NodeExpanded)
    def add_node_children(
        self, event: TreeBase.NodeExpanded[NodeData]
    ) -> None:
        self.add_status_dirs_in(tree_node=event.node)
        self.add_status_files_in(tree_node=event.node)
        if self.unchanged:
            self.add_dirs_without_status_in(tree_node=event.node)
            self.add_files_without_status_in(tree_node=event.node)

    def expand_all_nodes(self, node: TreeNode[NodeData]) -> None:
        # Recursively expand all directory nodes
        if node.data is not None and node.data.is_leaf is False:
            node.expand()
            self.add_status_dirs_in(tree_node=node)
            self.add_dirs_without_status_in(tree_node=node)
            for child in node.children:
                if child.data is not None and child.data.is_leaf is False:
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        expanded_nodes = self.get_expanded_nodes()
        for tree_node in expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(tree_node=tree_node)
            else:
                self.remove_files_without_status_in(tree_node=tree_node)


class FlatTree(TreeBase, AppType):

    destDir: reactive[Path | None] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, canvas_ids: CanvasIds) -> None:

        super().__init__(canvas_ids, tree_name=TreeName.flat_tree)

    def add_files_with_status(self) -> None:
        if self.active_canvas == Canvas.apply:
            status_files = self.app.chezmoi.all_status_files(
                active_canvas=Canvas.apply
            )
        else:
            status_files = self.app.chezmoi.all_status_files(
                active_canvas=Canvas.re_add
            )
        for file_path, status_code in status_files.items():
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code=status_code
            )
            if (
                self.active_canvas == Canvas.re_add
                and node_data.found is False
            ):
                continue
            node_label: Text = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )
        self.add_files_with_status()

    def watch_unchanged(self) -> None:
        if self.unchanged:
            self.add_files_without_status_in(tree_node=self.root)
        else:
            self.remove_files_without_status_in(tree_node=self.root)


class DoctorTable(DataTable[Text], AppType):

    def __init__(self) -> None:
        self.pw_mgr_commands: list[str] = []
        super().__init__(
            id=Id.config_tab.datatable_id,
            show_cursor=False,
            classes=Tcss.doctor_table.name,
        )

    def populate_doctor_data(self, doctor_data: list[str]) -> list[str]:
        # TODO: create reactive var to run this so the app reacts on chezmoi config changes while running
        self.dr_style = {
            "ok": self.app.theme_variables["text-success"],
            "info": self.app.theme_variables["foreground-darken-1"],
            "warning": self.app.theme_variables["text-warning"],
            "failed": self.app.theme_variables["text-error"],
            "error": self.app.theme_variables["text-error"],
        }

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
            id=Id.config_tab.listview_id, classes=Tcss.doctor_listview.name
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
