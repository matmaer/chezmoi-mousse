from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Switch, TabPane

from chezmoi_mousse import AppIds, DirContentBtn, TabLabel

from .common.actionables import OperateButtons, SwitchSlider
from .common.managed_tree import DestDirTree, ManagedTree
from .common.switchers import ViewSwitcher

__all__ = ["ReAddTab"]


class ReAddTab(TabPane):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=TabLabel.re_add, title=TabLabel.re_add)
        self.ids = ids

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(self.ids)
            yield Vertical(ViewSwitcher(self.ids), OperateButtons(self.ids))
        yield SwitchSlider(self.ids)

    def on_mount(self) -> None:
        self.managed_tree = self.query_one(self.ids.managed_tree_q, ManagedTree)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.ids.switch.unchanged:
            self.managed_tree.unchanged = event.value
        elif event.switch.id == self.ids.switch.expand_all:
            self.managed_tree.expand_all = event.value

    @on(DirContentBtn.Pressed)
    def handle_path_in_dir_node_pressed(self, event: DirContentBtn.Pressed) -> None:
        if isinstance(event.button, DirContentBtn):
            event.stop()
            self.managed_tree.show_requested_node(event.button.path)
