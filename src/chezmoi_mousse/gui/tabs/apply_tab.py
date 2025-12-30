from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from chezmoi_mousse import IDS, AppType, NodeData
from chezmoi_mousse.shared import (
    CurrentApplyNodeMsg,
    OperateButtons,
    OperateInfo,
)

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase

__all__ = ["ApplyTab"]


class ApplyTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.apply)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield OperateInfo(ids=IDS.apply)
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield ViewSwitcher(ids=IDS.apply)
        yield SwitchSlider(ids=IDS.apply)
        yield OperateButtons(IDS.apply)

    def on_mount(self) -> None:
        self.operate_info = self.query_one(
            IDS.apply.static.operate_info_q, Static
        )
        self.operate_info.display = False

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        self.current_node = msg.node_data
        self.update_view_node_data(msg.node_data)
