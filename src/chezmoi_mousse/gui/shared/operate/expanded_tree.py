from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive
from textual.widgets.tree import TreeNode

from chezmoi_mousse import NodeData, TreeName

from ._tree_widget import TreeWidget

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["ExpandedTree"]


class ExpandedTree(TreeWidget):

    destDir: reactive["Path | None"] = reactive(None, init=False)
    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.expanded_tree)

    def watch_destDir(self) -> None:
        if self.destDir is None:
            return
        self.root.data = NodeData(
            path=self.destDir, is_leaf=False, found=True, status="F"
        )
        self.expand_all_nodes(self.root)

    @on(TreeWidget.NodeExpanded)
    def add_node_children(
        self, event: TreeWidget.NodeExpanded[NodeData]
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
