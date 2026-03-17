from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Switch

from chezmoi_mousse import IDS, AppType, SwitchEnum, TabLabel

from .common.actionables import OperateButtons, SwitchSlider, TabButton
from .common.switchers import TreeSwitcher, ViewSwitcher

__all__ = ["ReAddTab"]


class ReAddTab(Container, AppType):

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TreeSwitcher(IDS.re_add)
            yield Vertical(ViewSwitcher(IDS.re_add), OperateButtons(IDS.re_add))
        yield SwitchSlider(IDS.re_add)

    def on_mount(self) -> None:
        self.tree_switcher = self.query_one(
            IDS.re_add.container.left_side_q, TreeSwitcher
        )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.re_add.switch.unchanged:
            self.tree_switcher.unchanged = event.value
        elif event.switch.id == IDS.re_add.switch.expand_all:
            self.tree_switcher.expand_all = event.value

    @on(TabButton.Pressed)
    def enable_disable_expand_all(self, event: TabButton.Pressed) -> None:
        event.stop()
        expand_all_switch = self.query_one(IDS.re_add.switch.expand_all_q, Switch)
        if event.button.label == TabLabel.tree:
            expand_all_switch.disabled = False
            expand_all_switch.tooltip = SwitchEnum.expand_all.enabled_tooltip
        elif event.button.label == TabLabel.list:
            expand_all_switch.disabled = True
            expand_all_switch.tooltip = SwitchEnum.expand_all.disabled_tooltip
