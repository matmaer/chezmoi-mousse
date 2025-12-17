from textual import on
from textual.app import ComposeResult
from textual.widgets import Button

from chezmoi_mousse import IDS, AppType, OperateBtn, PathKind
from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tab_horizontal import TabHorizontal

__all__ = ["ApplyTab"]


class ApplyTab(TabHorizontal, AppType):

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
        self.apply_btn = self.query_one(
            IDS.apply.operate_btn.apply_path_q, Button
        )

    @on(CurrentApplyNodeMsg)
    def update_apply_operate_buttons(self, msg: CurrentApplyNodeMsg) -> None:
        self.apply_btn.disabled = True
        self.apply_btn.tooltip = OperateBtn.apply_path.disabled_tooltip
        node_path = msg.node_data.path
        if msg.node_data.path_kind == PathKind.DIR:
            self.apply_btn.label = OperateBtn.apply_path.dir_label
            if (
                node_path in self.app.chezmoi.status_dirs
                or self.app.chezmoi.apply_status_files_in(node_path)
            ):
                self.apply_btn.disabled = False
                self.apply_btn.tooltip = OperateBtn.apply_path.dir_tooltip
        elif msg.node_data.path_kind == PathKind.FILE:
            self.apply_btn.label = OperateBtn.apply_path.file_label
            if node_path in self.app.chezmoi.apply_status_files:
                self.apply_btn.disabled = False
                self.apply_btn.tooltip = OperateBtn.apply_path.file_tooltip
        self.update_other_buttons(msg.node_data)
        self.update_view_node_data(msg.node_data)
