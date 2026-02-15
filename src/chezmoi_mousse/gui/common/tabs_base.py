"""Contains subclassed textual classes shared between the ApplyTab and ReAddTab."""

from textual import on
from textual.containers import Container
from textual.widgets import Button, ContentSwitcher, Switch

from chezmoi_mousse import AppIds, SubTabLabel, SwitchEnum, Tcss

# from chezmoi_mousse import AppIds, NodeData, SubTabLabel, SwitchEnum, Tcss

# from .views import ContentsView

__all__ = ["TabsBase"]


class TabsBase(Container):

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
