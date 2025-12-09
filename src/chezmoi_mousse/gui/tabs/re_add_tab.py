from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import IDS, OperateBtn, PathKind
from chezmoi_mousse.shared import CurrentReAddNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tab_horizontal import TabHorizontal

__all__ = ["ReAddTab"]


class ReAddTab(TabHorizontal):

    def __init__(self) -> None:
        super().__init__(ids=IDS.re_add)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(ids=IDS.re_add)
        yield ViewSwitcher(ids=IDS.re_add, diff_reverse=True)
        yield OperateButtons(
            ids=IDS.re_add,
            buttons=(
                OperateBtn.re_add_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ),
        )
        yield SwitchSlider(ids=IDS.re_add)

    @on(CurrentReAddNodeMsg)
    def update_re_add_operate_buttons(
        self, event: CurrentReAddNodeMsg
    ) -> None:
        self.update_view_path(event.node_data.path)
        operate_path_button = self.query_one(
            IDS.re_add.operate_btn.re_add_path_q, Button
        )
        operate_path_button.label = (
            OperateBtn.re_add_path.dir_label
            if event.node_data.path_kind == PathKind.DIR
            else OperateBtn.re_add_path.file_label
        )
        operate_path_button.tooltip = (
            OperateBtn.re_add_path.dir_tooltip
            if event.node_data.path_kind == PathKind.DIR
            else OperateBtn.re_add_path.file_tooltip
        )
        operate_path_button.disabled = (
            True if event.node_data.status in "X " else False
        )
        self.update_other_buttons(event.node_data)
