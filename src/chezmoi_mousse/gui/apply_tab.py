from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import OperateBtn, Switches

from .shared.button_groups import OperateBtnHorizontal
from .shared.operate_msg import CurrentApplyNodeMsg
from .shared.switch_slider import SwitchSlider
from .shared.switchers import TreeSwitcher, ViewSwitcher
from .shared.tabs_base import ApplyReAddTabsBase

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["ApplyTab"]


class ApplyTab(ApplyReAddTabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        self.operate_path_button_qid = ids.button_id(
            "#", btn=OperateBtn.apply_path
        )
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(self.ids)
        yield ViewSwitcher(ids=self.ids, diff_reverse=False)
        yield OperateBtnHorizontal(
            ids=self.ids,
            buttons=(
                OperateBtn.apply_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ),
        )
        yield SwitchSlider(
            ids=self.ids, switches=(Switches.unchanged, Switches.expand_all)
        )

    @on(CurrentApplyNodeMsg)
    def update_apply_operate_buttons(self, event: CurrentApplyNodeMsg) -> None:
        self.update_view_path(event.node_data.path)
        operate_path_button = self.query_one(
            self.operate_path_button_qid, Button
        )
        operate_path_button.label = (
            OperateBtn.apply_path.dir_label
            if event.node_data.path_type == "dir"
            else OperateBtn.apply_path.file_label
        )
        operate_path_button.tooltip = (
            OperateBtn.apply_path.dir_tooltip
            if event.node_data.path_type == "dir"
            else OperateBtn.apply_path.file_tooltip
        )
        operate_path_button.disabled = (
            True if event.node_data.status == "X" else False
        )
        self.update_other_buttons(event.node_data)
