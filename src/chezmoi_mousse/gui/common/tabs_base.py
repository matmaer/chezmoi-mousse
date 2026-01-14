"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from textual import on
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import AppIds, NodeData, SubTabLabel, SwitchEnum, Tcss

from .trees import ListTree, ManagedTree
from .views import ContentsView, DiffView, GitLogPath

__all__ = ["TabsBase"]


class TabsBase(Vertical):

    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__(id=ids.tab_id)

        self.ids = ids
        self.expand_all_state = False

    def update_view_node_data(self, node_data: "NodeData") -> None:
        contents_view = self.query_one(self.ids.container.contents_q, ContentsView)
        contents_view.node_data = node_data

        diff_view = self.query_one(self.ids.container.diff_q, DiffView)
        diff_view.node_data = node_data

        git_log_path = self.query_one(self.ids.container.git_log_path_q, GitLogPath)
        git_log_path.path = node_data.path

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

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.filter.unchanged:
            list_tree = self.query_one(self.ids.tree.list_q, ListTree)
            list_tree.unchanged = event.value

            managed_tree = self.query_one(self.ids.tree.managed_q, ManagedTree)
            managed_tree.unchanged = event.value
