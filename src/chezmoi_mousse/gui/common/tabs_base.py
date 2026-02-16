from pathlib import Path

from textual import on
from textual.containers import Container
from textual.widgets import Button, ContentSwitcher, Switch
from textual.widgets.tree import TreeNode

from chezmoi_mousse import AppIds, AppType, SubTabLabel, SwitchEnum, TabName, Tcss

from .trees import ManagedTree

__all__ = ["TabsBase"]


class TabsBase(Container, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.tab_id)
        self.ids = ids
        self.expand_all_state = False

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.label in (SubTabLabel.tree, SubTabLabel.list):
            # toggle expand all switch enabled disabled state
            tree_switcher = self.query_one(self.ids.switcher.trees_q, ContentSwitcher)
            expand_all_switch = self.query_one(self.ids.filter.expand_all_q, Switch)
            if event.button.label == SubTabLabel.tree:
                if self.expand_all_state is True:
                    tree_switcher.current = self.ids.tree.expanded
                else:
                    tree_switcher.current = self.ids.tree.managed
                expand_all_switch.disabled = False
                expand_all_switch.tooltip = SwitchEnum.expand_all.enabled_tooltip
            elif event.button.label == SubTabLabel.list:
                expand_all_switch.disabled = True
                expand_all_switch.tooltip = SwitchEnum.expand_all.disabled_tooltip
                tree_switcher.current = self.ids.tree.list

    def _get_expanded_nodes(self) -> dict[int, TreeNode[Path]]:
        managed_tree = self.query_one(self.ids.tree.managed_q, ManagedTree)
        managed_tree_expanded: dict[int, TreeNode[Path]] = {0: managed_tree.root}
        managed_tree_expanded.update(
            {
                node_id: tree_node
                for node_id, tree_node in managed_tree._tree_nodes.items()  # pyright: ignore[reportPrivateUsage]
                if tree_node.is_expanded
            }
        )
        return managed_tree_expanded

    @on(Switch.Changed)
    def handle_show_unchanged_switch(self, event: Switch.Changed) -> None:
        event.stop()
        dir_nodes = (
            self.app.parsed.apply_dir_nodes
            if self.ids.canvas_name == TabName.apply
            else self.app.parsed.re_add_dir_nodes
        )
        if (
            event.switch.id == self.ids.switch_id(switch=SwitchEnum.unchanged)
            and event.value is True
        ):
            managed_tree_expanded = self._get_expanded_nodes()
            for _, tree_node in managed_tree_expanded.items():
                if tree_node.data is None:
                    continue
                for x_file in dir_nodes[tree_node.data].x_files:
                    tree_node.add_leaf(x_file.name, x_file)
        elif (
            event.switch.id == self.ids.switch_id(switch=SwitchEnum.unchanged)
            and event.value is False
        ):
            managed_tree_expanded = self._get_expanded_nodes()
            for _, tree_node in managed_tree_expanded.items():
                if tree_node.data is None:
                    continue
                children_to_remove = [
                    child
                    for child in tree_node.children
                    if child.data in dir_nodes[tree_node.data].x_files
                ]
                for child in children_to_remove:
                    child.remove()
