from typing import TYPE_CHECKING

from textual import on
from textual.reactive import reactive

from chezmoi_mousse import NodeData, TreeName

from .tree_base import TreeBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["ManagedTree"]


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
