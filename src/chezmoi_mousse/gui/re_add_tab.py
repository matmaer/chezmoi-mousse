from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal

from chezmoi_mousse import IDS, AppType

from .common.actionables import OperateButtons, SwitchSlider
from .common.messages import CurrentReAddNodeMsg
from .common.operate_mode import OperateMode
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase

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

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(
        self, msg: CurrentReAddNodeMsg
    ) -> None:
        msg.stop()
        self.update_view_node_data(msg.node_data)
        self.operate_mode_container.path_arg = str(msg.node_data.path)
