from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal

from chezmoi_mousse import IDS, AppType

from .common.actionables import OperateButtons, SwitchSlider
from .common.messages import CurrentReAddNodeMsg
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase
from .common.views import ContentsView, DiffView, GitLog
from .operate_mode import OperateMode

__all__ = ["ReAddTab"]


class ReAddTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.re_add)

    def compose(self) -> ComposeResult:
        yield OperateMode(ids=IDS.re_add)
        with Horizontal():
            yield TreeSwitcher(ids=IDS.re_add)
            yield ViewSwitcher(ids=IDS.re_add)
        yield OperateButtons(IDS.re_add)
        yield SwitchSlider(ids=IDS.re_add)

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
        if self.app.paths is None:
            return
        self.git_log_view.git_log_result = self.app.paths.git_log_tables[
            msg.node_data.path
        ]
        self.diff_view.diff_widgets = self.app.paths.re_add_diff_widgets[
            msg.node_data.path
        ]
        self.operate_mode_container.path_arg = msg.node_data.path
        self.contents_view.content_widgets = self.app.paths.content_widgets[
            msg.node_data.path
        ].widget
