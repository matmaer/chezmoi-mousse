from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button

from chezmoi_mousse import IDS, AppType, OperateBtn, PathKind
from chezmoi_mousse._operate_button_data import OpBtnLabels
from chezmoi_mousse.shared import CurrentReAddNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_container import TabVertical

__all__ = ["ReAddTab"]


class ReAddTab(TabVertical, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.re_add)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield TreeSwitcher(ids=IDS.re_add)
            yield ViewSwitcher(ids=IDS.re_add, diff_reverse=True)
        yield OperateButtons(ids=IDS.re_add)
        yield SwitchSlider(ids=IDS.re_add)

    def on_mount(self) -> None:
        self.operate_buttons = self.query_one(
            IDS.re_add.container.operate_buttons_q, OperateButtons
        )
        self.operate_buttons.update_buttons(
            (
                OperateBtn.re_add_path,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            )
        )
        self.re_add_btn = self.query_one(
            IDS.re_add.operate_btn.re_add_path_q, Button
        )

    @on(CurrentReAddNodeMsg)
    def update_re_add_operate_buttons(self, msg: CurrentReAddNodeMsg) -> None:
        self.re_add_btn.disabled = True
        node_path = msg.node_data.path
        if msg.node_data.path_kind == PathKind.DIR:
            self.re_add_btn.label = OpBtnLabels.re_add_dir
            if (
                node_path in self.app.chezmoi.status_dirs
                or self.app.chezmoi.apply_status_files_in(node_path)
            ):
                self.re_add_btn.disabled = False
        elif msg.node_data.path_kind == PathKind.FILE:
            self.re_add_btn.label = OpBtnLabels.re_add_file
            if node_path in self.app.chezmoi.apply_status_files:
                self.re_add_btn.disabled = False
        self.update_other_buttons(msg.node_data)
        self.update_view_node_data(msg.node_data)
