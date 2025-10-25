from pathlib import Path
from typing import TYPE_CHECKING

from rich.style import Style
from rich.text import Text
from textual import on
from textual.events import Key
from textual.widgets import Tree
from textual.widgets._tree import TOGGLE_STYLE
from textual.widgets.tree import TreeNode

from chezmoi_mousse import (
    AppType,
    Canvas,
    Chars,
    NodeData,
    PaneBtn,
    Tcss,
    TreeName,
)

from .operate_msg import TreeNodeSelectedMsg

if TYPE_CHECKING:
    from chezmoi_mousse import ActiveCanvas, CanvasIds


__all__ = ["TreeBase"]


class TreeBase(Tree[NodeData], AppType):

    destDir: "Path"

    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self, ids: "CanvasIds", *, tree_name: TreeName) -> None:
        self.tree_name = tree_name
        self.ids = ids
        self._initial_render = True
        self._first_focus = True
        self._user_interacted = False
        if self.ids.canvas_name == Canvas.apply:
            self.active_canvas: "ActiveCanvas" = Canvas.apply
        else:
            self.active_canvas: "ActiveCanvas" = Canvas.re_add

        self.root_data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )
        super().__init__(
            label="root",
            id=self.ids.tree_id(tree=self.tree_name),
            classes=Tcss.tree_widget.name,
            data=self.root_data,
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
        styled = "white"
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
        self, *, path: "Path", is_leaf: bool, status_code: str
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

    def _get_existing_paths(
        self, tree_node: TreeNode[NodeData], is_leaf: bool
    ) -> list["Path"]:
        # get existing nodes (files or dirs based on is_leaf)
        return [
            child.data.path
            for child in tree_node.children
            if child.data is not None and child.data.is_leaf is is_leaf
        ]

    def _create_and_add_node(
        self,
        tree_node: TreeNode[NodeData],
        path: "Path",
        status_code: str,
        is_leaf: bool,
    ) -> None:
        node_data: NodeData = self.create_node_data(
            path=path, is_leaf=is_leaf, status_code=status_code
        )
        node_label: Text = self.style_label(node_data)
        if is_leaf:
            tree_node.add_leaf(label=node_label, data=node_data)
        else:
            tree_node.add(label=node_label, data=node_data)

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
        if tree_node.data is None:
            return

        existing_leaves = self._get_existing_paths(tree_node, is_leaf=True)

        if self.tree_name == TreeName.list_tree:
            status_files = self.app.chezmoi.all_status_files(
                self.active_canvas
            )
        else:
            status_files = self.app.chezmoi.status_files_in(
                self.active_canvas, tree_node.data.path
            )

        for file_path, status_code in status_files.items():
            if file_path in existing_leaves:
                continue
            # Only call exists() in re_add canvas
            if (
                self.active_canvas == PaneBtn.re_add_tab
                and not file_path.exists()
            ):
                continue
            self._create_and_add_node(
                tree_node, file_path, status_code, is_leaf=True
            )

    def add_files_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            return

        # Both paths cached in the Chezmoi instance, don't cache this here as
        # we update the cache there after a WriteCmd.
        if self.active_canvas == Canvas.apply:
            paths = self.app.chezmoi.managed_paths.apply_files_without_status
        else:
            paths = self.app.chezmoi.managed_paths.re_add_files_without_status

        files_without_status = {
            path: "X" for path in paths if path.parent == tree_node.data.path
        }

        existing_leaves = self._get_existing_paths(tree_node, is_leaf=True)
        for file_path, status_code in files_without_status.items():
            if file_path in existing_leaves:
                continue
            # Only call exists() in re_add canvas
            if (
                self.active_canvas == PaneBtn.re_add_tab
                and not file_path.exists()
            ):
                continue
            self._create_and_add_node(
                tree_node, file_path, status_code, is_leaf=True
            )

    def add_status_dirs_in(self, *, tree_node: TreeNode[NodeData]) -> None:
        if tree_node.data is None:
            return

        existing_dirs = self._get_existing_paths(tree_node, is_leaf=False)
        dir_paths = self.app.chezmoi.status_dirs_in(
            self.active_canvas, tree_node.data.path
        )

        for dir_path, status_code in dir_paths.items():
            if dir_path in existing_dirs:
                continue
            self._create_and_add_node(
                tree_node, dir_path, status_code, is_leaf=False
            )

    def add_dirs_without_status_in(
        self, *, tree_node: TreeNode[NodeData]
    ) -> None:
        if tree_node.data is None:
            return

        existing_dirs = self._get_existing_paths(tree_node, is_leaf=False)
        dir_paths = self.app.chezmoi.dirs_without_status_in(
            self.active_canvas, tree_node.data.path
        )

        for dir_path, status_code in dir_paths.items():
            if dir_path in existing_dirs:
                continue
            self._create_and_add_node(
                tree_node, dir_path, status_code, is_leaf=False
            )

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
