from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from chezmoi_mousse import IDS, AppType, NodeData
from chezmoi_mousse.shared import (
    CurrentReAddNodeMsg,
    OperateButtons,
    OperateInfo,
)

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase

__all__ = ["ReAddTab"]


class ReAddTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.re_add)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield OperateInfo(ids=IDS.re_add)
        with Horizontal():
            yield TreeSwitcher(ids=IDS.re_add)
            yield ViewSwitcher(ids=IDS.re_add)
        yield OperateButtons(IDS.re_add)
        yield SwitchSlider(ids=IDS.re_add)

    def on_mount(self) -> None:
        self.operate_info = self.query_one(
            IDS.re_add.static.operate_info_q, Static
        )
        self.operate_info.display = False

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(
        self, msg: CurrentReAddNodeMsg
    ) -> None:
        self.update_view_node_data(msg.node_data)
