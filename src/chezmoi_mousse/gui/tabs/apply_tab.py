from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button

from chezmoi_mousse import IDS, AppType, OpBtnLabels, PathKind
from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_container import TabVertical

__all__ = ["ApplyTab"]


class ApplyTab(TabVertical, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.apply)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield ViewSwitcher(ids=IDS.apply, diff_reverse=False)
        yield OperateButtons(ids=IDS.apply)
        yield SwitchSlider(ids=IDS.apply)

    def on_mount(self) -> None:
        self.operate_buttons = self.query_one(
            IDS.apply.container.operate_buttons_q, OperateButtons
        )
        self.apply_btn = self.query_one(
            IDS.apply.operate_btn.apply_path_q, Button
        )
        self.apply_btn.display = True
        self.forget_btn = self.query_one(
            IDS.apply.operate_btn.forget_path_q, Button
        )
        self.forget_btn.display = True
        self.destroy_btn = self.query_one(
            IDS.apply.operate_btn.destroy_path_q, Button
        )
        self.destroy_btn.display = True
        self.apply_btn = self.query_one(
            IDS.apply.operate_btn.apply_path_q, Button
        )

    @on(CurrentApplyNodeMsg)
    def update_apply_operate_buttons(self, msg: CurrentApplyNodeMsg) -> None:
        self.apply_btn.disabled = True
        node_path = msg.node_data.path
        if msg.node_data.path_kind == PathKind.DIR:
            self.apply_btn.label = OpBtnLabels.apply_dir
            if (
                node_path in self.app.chezmoi.status_dirs
                or self.app.chezmoi.apply_status_files_in(node_path)
            ):
                self.apply_btn.disabled = False
                self.apply_btn.tooltip = None
        elif msg.node_data.path_kind == PathKind.FILE:
            self.apply_btn.label = OpBtnLabels.apply_file
            if node_path in self.app.chezmoi.apply_status_files:
                self.apply_btn.disabled = False
                self.apply_btn.tooltip = None
        self.update_other_buttons(msg.node_data)
        self.update_view_node_data(msg.node_data)
