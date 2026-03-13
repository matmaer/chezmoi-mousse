from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Switch

from chezmoi_mousse import CMD, IDS, AppType, SwitchEnum, TabLabel

from .common.actionables import OperateButtons, SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher

__all__ = ["ReAddTab"]


class ReAddTab(Container, AppType):

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TreeSwitcher(IDS.re_add)
            yield Vertical(ViewSwitcher(IDS.re_add), OperateButtons(IDS.re_add))
        yield SwitchSlider(IDS.re_add)

    def on_mount(self) -> None:
        if CMD.cache.no_status_paths:
            self.app.call_later(self.toggle_unchanged)

    def toggle_unchanged(self) -> None:
        unchanged_switch = self.query_one(IDS.re_add.switch.unchanged_q, Switch)
        unchanged_switch.toggle()

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree_switcher = self.query_exactly_one(TreeSwitcher)
        if event.switch.id == IDS.re_add.switch_id(switch=SwitchEnum.unchanged):
            tree_switcher.unchanged = event.value
        elif event.switch.id == IDS.re_add.switch_id(switch=SwitchEnum.expand_all):
            tree_switcher.expand_all = event.value

    @on(Button.Pressed)
    def switch_view(self, event: Button.Pressed) -> None:
        if event.button.label not in (TabLabel.list, TabLabel.tree):
            return
        expand_all_switch = self.query_one(IDS.re_add.switch.expand_all_q, Switch)
        if event.button.label == TabLabel.list:
            expand_all_switch.disabled = False
            expand_all_switch.tooltip = SwitchEnum.expand_all.enabled_tooltip
        elif event.button.label == TabLabel.list:
            expand_all_switch.disabled = True
            expand_all_switch.tooltip = SwitchEnum.expand_all.disabled_tooltip
