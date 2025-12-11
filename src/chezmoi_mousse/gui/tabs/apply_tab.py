from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import IDS, OperateBtn, PathKind
from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tab_horizontal import TabHorizontal

__all__ = ["ApplyTab"]


class ApplyTab(TabHorizontal):

    def __init__(self) -> None:
        super().__init__(ids=IDS.apply)

    def compose(self) -> ComposeResult:
        yield TreeSwitcher(IDS.apply)
        yield ViewSwitcher(ids=IDS.apply, diff_reverse=False)
        yield OperateButtons(
            ids=IDS.apply,
            buttons=(
                OperateBtn.apply_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ),
        )
        yield SwitchSlider(ids=IDS.apply)

    def on_mount(self) -> None:
        self.op_path_btn = self.query_one(
            IDS.apply.operate_btn.apply_path_q, Button
        )

    @on(CurrentApplyNodeMsg)
    def update_apply_operate_buttons(self, event: CurrentApplyNodeMsg) -> None:
        self.update_view_path(event.node_data.path)
        self.op_path_btn.label = (
            OperateBtn.apply_path.dir_label
            if event.node_data.path_kind == PathKind.DIR
            else OperateBtn.apply_path.file_label
        )
        if event.node_data.status == "X":
            self.op_path_btn.disabled = True
            self.op_path_btn.tooltip = OperateBtn.apply_path.disabled_tooltip
        else:
            self.op_path_btn.disabled = False
            self.op_path_btn.tooltip = (
                OperateBtn.apply_path.dir_tooltip
                if event.node_data.path_kind == PathKind.DIR
                else OperateBtn.apply_path.file_tooltip
            )
        self.update_other_buttons(event.node_data)
