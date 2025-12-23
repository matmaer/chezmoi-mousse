from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from chezmoi_mousse import IDS, AppType, NodeData, PathKind, Tcss
from chezmoi_mousse._operate_button_data import OpBtnLabels
from chezmoi_mousse.shared import CurrentReAddNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_container import TabVertical

__all__ = ["ReAddTab"]


class ReAddTab(TabVertical, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.re_add)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield Static(
            id=IDS.re_add.static.operate_info, classes=Tcss.operate_info
        )
        with Horizontal():
            yield TreeSwitcher(ids=IDS.re_add)
            yield ViewSwitcher(ids=IDS.re_add, diff_reverse=True)
        yield OperateButtons(ids=IDS.re_add)
        yield SwitchSlider(ids=IDS.re_add)

    def on_mount(self) -> None:
        self.operate_buttons = self.query_one(
            IDS.re_add.container.operate_buttons_q, OperateButtons
        )
        self.re_add_btn = self.query_one(
            IDS.re_add.operate_btn.re_add_path_q, Button
        )
        self.re_add_btn.display = True
        self.forget_btn = self.query_one(
            IDS.re_add.operate_btn.forget_path_q, Button
        )
        self.forget_btn.display = True
        self.destroy_btn = self.query_one(
            IDS.re_add.operate_btn.destroy_path_q, Button
        )
        self.destroy_btn.display = True
        self.re_add_btn = self.query_one(
            IDS.re_add.operate_btn.re_add_path_q, Button
        )
        self.operate_info = self.query_one(
            IDS.re_add.static.operate_info_q, Static
        )
        self.operate_info.display = False

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
