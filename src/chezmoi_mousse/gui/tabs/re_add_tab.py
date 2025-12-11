from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import IDS, AppType, OperateBtn, PathKind
from chezmoi_mousse.shared import CurrentReAddNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tab_horizontal import TabHorizontal

__all__ = ["ReAddTab"]


class ReAddTab(TabHorizontal, AppType):

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

    def on_mount(self) -> None:
        self.op_path_btn = self.query_one(
            IDS.re_add.operate_btn.re_add_path_q, Button
        )

    @on(CurrentReAddNodeMsg)
    def update_re_add_operate_buttons(
        self, event: CurrentReAddNodeMsg
    ) -> None:
        self.update_view_path(event.node_data.path)
        self.op_path_btn.label = (
            OperateBtn.re_add_path.dir_label
            if event.node_data.path_kind == PathKind.DIR
            else OperateBtn.re_add_path.file_label
        )
        if event.node_data.status in "X ":
            if event.node_data.path_kind is PathKind.DIR:
                if self.app.chezmoi.has_re_add_status_paths_in(
                    event.node_data.path
                ):
                    self.op_path_btn.disabled = False
                    self.op_path_btn.tooltip = (
                        OperateBtn.re_add_path.dir_tooltip
                    )
                else:
                    self.op_path_btn.disabled = True
                    self.op_path_btn.tooltip = (
                        OperateBtn.re_add_path.disabled_tooltip
                    )
            elif event.node_data.path_kind is PathKind.FILE:
                self.op_path_btn.disabled = False
                self.op_path_btn.tooltip = OperateBtn.re_add_path.file_tooltip
        else:
            self.op_path_btn.disabled = False
            self.op_path_btn.tooltip = (
                OperateBtn.re_add_path.dir_tooltip
                if event.node_data.path_kind == PathKind.DIR
                else OperateBtn.re_add_path.file_tooltip
            )
        self.update_other_buttons(event.node_data)
