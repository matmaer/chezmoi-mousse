"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from pathlib import Path

from textual.reactive import reactive
from textual.widgets import Tree

from chezmoi_mousse import AppIds, AppType, Chars, NodeData, Tcss, TreeName

type NodeDict = dict[Path, NodeData]


class TreeBase(Tree[NodeData], AppType):

    ICON_NODE = Chars.tree_collapsed
    ICON_NODE_EXPANDED = Chars.tree_expanded

    unchanged: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds", *, tree_name: TreeName) -> None:
        super().__init__(
            label="root", id=ids.tree_id(tree=tree_name), classes=Tcss.tree_widget
        )
        self.ids = ids


class ListTree(TreeBase):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.list_tree)

    # will be implemented later after ManagedTree and ExpandedTree are done
    def populate_dest_dir(self) -> None:
        pass


class ManagedTree(TreeBase):

    def __init__(self, *, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(self.ids, tree_name=TreeName.managed_tree)

    def populate_dest_dir(self) -> None:
        self.expanded_nodes = [self.root]
