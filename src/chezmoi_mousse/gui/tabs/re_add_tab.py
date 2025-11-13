from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import OperateBtn

from ..shared.buttons import OperateButtons
from ..shared.operate_msg import CurrentReAddNodeMsg
from .shared.switch_slider import SwitchSlider
from .shared.switchers import TreeSwitcher, ViewSwitcher
from .shared.tabs_base import ApplyReAddTabsBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["ReAddTab"]


class ReAddTab(ApplyReAddTabsBase):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

        self.operate_path_button_qid = self.ids.button_id(
            "#", btn=OperateBtn.re_add_path
        )

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(ids=self.ids)
        yield ViewSwitcher(ids=self.ids, diff_reverse=True)
        yield OperateButtons(
            ids=self.ids,
            buttons=(
                OperateBtn.re_add_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ),
        )
        yield SwitchSlider(ids=self.ids)

    @on(CurrentReAddNodeMsg)
    def update_re_add_operate_buttons(
        self, event: CurrentReAddNodeMsg
    ) -> None:
        self.update_view_path(event.node_data.path)
        operate_path_button = self.query_one(
            self.operate_path_button_qid, Button
        )
        operate_path_button.label = OperateBtn.re_add_path.label(
            event.node_data.path_type
        )
        operate_path_button.tooltip = (
            OperateBtn.re_add_path.dir_tooltip
            if event.node_data.path_type == "dir"
            else OperateBtn.re_add_path.file_tooltip
        )
        operate_path_button.disabled = (
            True if event.node_data.status in "X " else False
        )
        self.update_other_buttons(event.node_data)
