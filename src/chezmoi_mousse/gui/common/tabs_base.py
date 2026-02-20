from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import Container
from textual.widgets import Switch
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppType, DirNode, SwitchEnum, TabName

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

from .trees import ListTree, ManagedTree

__all__ = ["TabsBase"]


class TabsBase(Container, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.tab_id)
        self.ids = ids
        self.expand_all_state = False
        self.old_expanded_nodes: list[TreeNode[Path]] = []

    @property
    def dir_nodes(self) -> dict[Path, DirNode]:
        if self.ids.canvas_name == TabName.apply:
            return self.app.apply_dir_nodes
        else:
            return self.app.re_add_dir_nodes

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch_id(switch=SwitchEnum.unchanged):
            self.shouw_unchanged_state = event.value
            self.handle_unchanged_switch(event)
        elif event.switch.id == self.ids.switch_id(switch=SwitchEnum.expand_all):
            self.handle_expand_all_switch(event)

    def handle_expand_all_switch(self, event: Switch.Changed) -> None:
        managed_tree = self.query_one(self.ids.tree.managed_q, ManagedTree)
        managed_tree_nodes = managed_tree.get_all_nodes()
        if event.value is True:
            self.expand_all_state = True
            self.old_expanded_nodes = [
                node for node in managed_tree_nodes if node.is_expanded
            ]
            for node in managed_tree_nodes:
                node.expand()
        else:
            self.expand_all_state = False
            for node in managed_tree_nodes:
                if node not in self.old_expanded_nodes:
                    node.collapse()

    def handle_unchanged_switch(self, event: Switch.Changed) -> None:
        def add_managed_tree_nodes() -> None:
            for x_dir in self.app.tree_x_dirs:
                parent_tree_node = next(
                    (node for node in managed_tree_nodes if node.data == x_dir.parent),
                    None,
                )
                if parent_tree_node is not None:
                    new_x_node = parent_tree_node.add(
                        f"[dim]{x_dir.name}[/]", data=x_dir
                    )
                    if self.expand_all_state:
                        new_x_node.expand()
                    for x_file in self.dir_nodes[x_dir].x_files_in:
                        new_x_node.add_leaf(f"[dim]{x_file.name}[/]", x_file)
                    parent_tree_node.expand()

        def add_list_tree_nodes() -> None:
            for x_file in self.app.x_files:
                rel_path = str(x_file.relative_to(self.app.dest_dir))
                list_tree.root.add_leaf(f"[dim]{rel_path}[/]", x_file)

        list_tree = self.query_one(self.ids.tree.list_q, ListTree)
        list_tree_nodes = list_tree.get_all_nodes()
        managed_tree = self.query_one(self.ids.tree.managed_q, ManagedTree)
        managed_tree_nodes = managed_tree.get_all_nodes()
        if event.value is True:
            add_managed_tree_nodes()
            add_list_tree_nodes()
        elif event.value is False:
            # remove x_files and x_dirs from managed tree
            for tree_node in managed_tree_nodes:
                if (
                    tree_node.data in self.app.x_files
                    or tree_node.data in self.app.tree_x_dirs
                ):
                    try:
                        tree_node.remove()
                    except ValueError:
                        pass
            # remove x_files from list tree
            for tree_node in list_tree_nodes:
                if tree_node.data in self.app.x_files:
                    tree_node.remove()
