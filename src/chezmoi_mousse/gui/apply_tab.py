from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Switch

from chezmoi_mousse import IDS, AppType, SwitchEnum

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.git_log import GitLog
from .common.messages import CurrentApplyNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher
from .operate_mode import OperateMode

__all__ = ["ApplyTab"]


class ApplyTab(Container, AppType):

    def compose(self) -> ComposeResult:
        yield OperateMode(IDS.apply)
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield Vertical(ViewSwitcher(IDS.apply), OperateButtons(IDS.apply))
        yield SwitchSlider(IDS.apply)

    def on_mount(self) -> None:
        self.operate_mode_container = self.query_one(
            IDS.apply.container.op_mode_q, OperateMode
        )
        self.contents_view = self.query_one(
            IDS.apply.container.contents_q, ContentsView
        )
        self.git_log_view = self.query_one(IDS.apply.container.git_log_q, GitLog)
        self.diff_view = self.query_one(IDS.apply.container.diff_q, DiffView)

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.git_log_view.show_path = msg.path
        self.operate_mode_container.path_arg = msg.path
        self.diff_view.show_path = msg.path
        self.contents_view.show_path = msg.path

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree_switcher = self.query_exactly_one(TreeSwitcher)
        if event.switch.id == IDS.apply.switch_id(switch=SwitchEnum.unchanged):
            tree_switcher.unchanged = event.value
        elif event.switch.id == IDS.apply.switch_id(switch=SwitchEnum.expand_all):
            tree_switcher.expand_all = event.value
