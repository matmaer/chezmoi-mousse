from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal

from chezmoi_mousse import IDS, AppType

from .common.actionables import OperateButtons, SwitchSlider
from .common.messages import CurrentApplyNodeMsg
from .common.operate_mode import OperateMode
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase

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

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.update_view_node_data(msg.node_data)
        self.operate_mode_container.path_arg = str(msg.node_data.path)
