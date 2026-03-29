from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Switch

from chezmoi_mousse import IDS, AppType, DirContentBtn

from .common.actionables import OperateButtons, SwitchSlider
from .common.managed_tree import DestDirTree, ManagedTree
from .common.switchers import ViewSwitcher

__all__ = ["ApplyTab"]


class ApplyTab(Container, AppType):

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield DestDirTree(IDS.apply)
            yield Vertical(ViewSwitcher(IDS.apply), OperateButtons(IDS.apply))
        yield SwitchSlider(IDS.apply)

    def on_mount(self) -> None:
        self.managed_tree = self.query_one(IDS.apply.managed_tree_q, ManagedTree)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == IDS.apply.switch.unchanged:
            self.managed_tree.unchanged = event.value
        elif event.switch.id == IDS.apply.switch.expand_all:
            self.managed_tree.expand_all = event.value

    @on(DirContentBtn.Pressed)
    def handle_path_in_dir_node_pressed(self, event: DirContentBtn.Pressed) -> None:
        if isinstance(event.button, DirContentBtn):
            event.stop()
            self.managed_tree.select_node_by_path(event.button.path)
