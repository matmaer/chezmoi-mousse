from pathlib import Path

from textual import on
from textual.containers import Container
from textual.widgets import Switch
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppIds, AppType, DirNode, SwitchEnum, TabName

from .trees import ManagedTree

__all__ = ["TabsBase"]


class TabsBase(Container, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.tab_id)
        self.ids = ids
        self.show_unchanged_state = False
        self.expand_all_state = False

    def _get_expanded_nodes(self) -> dict[int, TreeNode[Path]]:
        managed_tree = self.query_one(self.ids.tree.managed_q, ManagedTree)
        return managed_tree.expanded_nodes

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
            self.handle_unchanged_switch(event)
        elif event.switch.id == self.ids.switch_id(switch=SwitchEnum.expand_all):
            self.handle_expand_all_switch(event)

    def handle_expand_all_switch(self, event: Switch.Changed) -> None:
        if event.value is True:
            self.expand_all_state = True
            self.notify("Switch on: expand all")
        else:
            self.expand_all_state = False
            self.notify("Switch off: expand all")

    def handle_unchanged_switch(self, event: Switch.Changed) -> None:
        if event.value is True:
            self.show_unchanged_state = True
            for _, tree_node in self._get_expanded_nodes().items():
                if tree_node.data is None:
                    return
                for x_file in self.dir_nodes[tree_node.data].x_files_in:
                    tree_node.add_leaf(x_file.name, x_file)
        elif event.value is False:
            self.show_unchanged_state = False
            for _, tree_node in self._get_expanded_nodes().items():
                if tree_node.data is None:
                    return
                # retrieve the TreeNode objects of the unchanged files and remove them
                # from the tree.
                unchanged_files = self.dir_nodes[tree_node.data].x_files_in
                for unchanged_file in unchanged_files:
                    for child in tree_node.children:
                        if child.data == unchanged_file:
                            child.remove()
                            break
