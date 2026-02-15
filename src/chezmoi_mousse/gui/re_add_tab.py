from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal

from chezmoi_mousse import IDS, AppType

from .common.actionables import OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.git_log import GitLog
from .common.messages import CurrentReAddNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase
from .operate_mode import OperateMode

__all__ = ["ReAddTab"]


class ReAddTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(IDS.re_add)

    def compose(self) -> ComposeResult:
        yield OperateMode(IDS.re_add)
        with Horizontal():
            yield TreeSwitcher(IDS.re_add)
            yield ViewSwitcher(IDS.re_add)
        yield OperateButtons(IDS.re_add)
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

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(self, msg: CurrentReAddNodeMsg) -> None:
        msg.stop()
        self.git_log_view.show_path = msg.path
        self.diff_view.show_path = msg.path
        self.operate_mode_container.path_arg = msg.path
        self.contents_view.show_path = msg.path
