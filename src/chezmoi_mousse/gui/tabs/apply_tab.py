from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import OperateBtn
from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tab_horizontal import TabHorizontal

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["ApplyTab"]


class ApplyTab(TabHorizontal):

    def __init__(self, ids: "AppIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(self.ids)
        yield ViewSwitcher(ids=self.ids, diff_reverse=False)
        yield OperateButtons(
            ids=self.ids,
            buttons=(
                OperateBtn.apply_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ),
        )
        yield SwitchSlider(ids=self.ids)

    @on(CurrentApplyNodeMsg)
    def update_apply_operate_buttons(self, event: CurrentApplyNodeMsg) -> None:
        self.update_view_path(event.node_data.path)
        operate_path_button = self.query_one(
            self.ids.operate_btn.apply_path_q, Button
        )
        operate_path_button.label = OperateBtn.apply_path.label(
            event.node_data.path_type
        )
        operate_path_button.tooltip = OperateBtn.apply_path.tooltip(
            event.node_data.path_type
        )
        operate_path_button.disabled = (
            True if event.node_data.status == "X" else False
        )
        self.update_other_buttons(event.node_data)
