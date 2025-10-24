from typing import TYPE_CHECKING

from rich.text import Text
from textual import on
from textual.reactive import reactive
from textual.widgets.tree import TreeNode

from chezmoi_mousse import Canvas, NodeData, TreeName

from .tree_base import TreeBase

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CanvasIds

__all__ = ["ManagedTree"]


class ExpandedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.expanded_tree)

    def populate_tree(self) -> None:
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
        assert node.data is not None
        if node.data.is_leaf is False:
            self.add_status_dirs_in(tree_node=node)
            self.add_status_files_in(tree_node=node)
            for child in node.children:
                if child.data is not None and child.data.is_leaf is False:
                    child.expand()
                    self.expand_all_nodes(child)

    def watch_unchanged(self) -> None:
        expanded_nodes = self.get_expanded_nodes()
        for tree_node in expanded_nodes:
            if self.unchanged:
                self.add_files_without_status_in(tree_node=tree_node)
            else:
                self.remove_files_without_status_in(tree_node=tree_node)


class ListTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

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

    def add_files_without_status(self) -> None:
        if self.active_canvas == Canvas.apply:
            self.files_without_status: list["Path"] = (
                self.app.chezmoi.apply_files_without_status
            )
        else:
            self.files_without_status: list["Path"] = (
                self.app.chezmoi.re_add_files_without_status
            )
        for file_path in self.files_without_status:
            node_data: NodeData = self.create_node_data(
                path=file_path, is_leaf=True, status_code="X"
            )
            if (
                self.active_canvas == Canvas.re_add
                and node_data.found is False
            ):
                continue
            node_label: Text = self.style_label(node_data)
            self.root.add_leaf(label=node_label, data=node_data)

    def watch_unchanged(self) -> None:
        if self.unchanged:
            self.add_files_without_status()
        else:
            self.remove_files_without_status_in(tree_node=self.root)


class ManagedTree(TreeBase):

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, *, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def populate_tree(self) -> None:
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
