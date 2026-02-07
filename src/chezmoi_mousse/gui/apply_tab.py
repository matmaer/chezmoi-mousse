from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal

from chezmoi_mousse import IDS, AppType

from .common.actionables import OperateButtons, SwitchSlider
from .common.messages import CurrentApplyNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase
from .common.views import ContentsView, DiffView, GitLog
from .operate_mode import OperateMode

__all__ = ["ApplyTab"]


class ApplyTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.apply)

    def compose(self) -> ComposeResult:
        yield OperateMode(ids=IDS.apply)
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield ViewSwitcher(ids=IDS.apply)
        yield SwitchSlider(ids=IDS.apply)
        yield OperateButtons(IDS.apply)

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
        if self.app.paths is None:
            return
        self.git_log_view.git_log_result = self.app.paths.git_log_tables[
            msg.node_data.path
        ]
        self.operate_mode_container.path_arg = msg.node_data.path
        self.diff_view.diff_widgets = self.app.paths.apply_diff_widgets[
            msg.node_data.path
        ]
        self.contents_view.path = msg.node_data.path
