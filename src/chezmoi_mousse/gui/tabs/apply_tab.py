from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal

from chezmoi_mousse import IDS, AppType
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

    def compose(self) -> ComposeResult:
        yield OperateInfo(ids=IDS.apply)
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield ViewSwitcher(ids=IDS.apply)
        yield SwitchSlider(ids=IDS.apply)
        yield OperateButtons(IDS.apply)

    def on_mount(self) -> None:
        self.operate_info = self.query_one(
            IDS.apply.container.operate_info_q, OperateInfo
        )

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.update_view_node_data(msg.node_data)
        self.operate_info.path_arg = str(msg.node_data.path)
