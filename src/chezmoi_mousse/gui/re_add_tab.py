from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Switch

from chezmoi_mousse import IDS, AppType, SwitchEnum

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.git_log import GitLog
from .common.messages import CurrentReAddNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher
from .operate_mode import OperateMode

__all__ = ["ReAddTab"]


class ReAddTab(Container, AppType):

    def compose(self) -> ComposeResult:
        yield OperateMode(IDS.re_add)
        with Horizontal():
            yield TreeSwitcher(IDS.re_add)
            yield Vertical(ViewSwitcher(IDS.re_add), OperateButtons(IDS.re_add))
        yield SwitchSlider(IDS.re_add)

    def on_mount(self) -> None:
        self.operate_mode_container = self.query_one(
            IDS.re_add.container.op_mode_q, OperateMode
        )
        self.git_log_view = self.query_one(IDS.re_add.container.git_log_q, GitLog)
        self.contents_view = self.query_one(
            IDS.re_add.container.contents_q, ContentsView
        )
        self.diff_view = self.query_one(IDS.re_add.container.diff_q, DiffView)
        if self.app.no_status_paths:
            self.app.call_later(self.toggle_unchanged)

    def toggle_unchanged(self) -> None:
        unchanged_switch = self.query_one(IDS.re_add.switch.unchanged_q, Switch)
        unchanged_switch.toggle()
        managed_tree = self.query_one(IDS.re_add.tree.managed_q)
        managed_tree.refresh()

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(self, msg: CurrentReAddNodeMsg) -> None:
        msg.stop()
        self.git_log_view.show_path = msg.path
        self.diff_view.show_path = msg.path
        self.operate_mode_container.path_arg = msg.path
        self.contents_view.show_path = msg.path

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        tree_switcher = self.query_exactly_one(TreeSwitcher)
        if event.switch.id == IDS.re_add.switch_id(switch=SwitchEnum.unchanged):
            tree_switcher.unchanged = event.value
        elif event.switch.id == IDS.re_add.switch_id(switch=SwitchEnum.expand_all):
            tree_switcher.expand_all = event.value
