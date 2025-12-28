from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from chezmoi_mousse import IDS, AppType, NodeData, Tcss
from chezmoi_mousse.shared import CurrentReAddNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase

__all__ = ["ReAddTab"]


class ReAddTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.re_add)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield Static(
            id=IDS.re_add.static.operate_info, classes=Tcss.operate_info
        )
        with Horizontal():
            yield TreeSwitcher(ids=IDS.re_add)
            yield ViewSwitcher(ids=IDS.re_add)
        yield OperateButtons(IDS.re_add)
        yield SwitchSlider(ids=IDS.re_add)

    def on_mount(self) -> None:
        self.re_add_btn = self.query_one(
            IDS.re_add.op_btn.re_add_path_q, Button
        )
        self.forget_btn = self.query_one(
            IDS.re_add.op_btn.forget_path_q, Button
        )
        self.destroy_btn = self.query_one(
            IDS.re_add.op_btn.destroy_path_q, Button
        )
        self.exit_btn = self.query_one(
            IDS.re_add.op_btn.operate_exit_q, Button
        )
        self.operate_info = self.query_one(
            IDS.re_add.static.operate_info_q, Static
        )
        self.operate_info.display = False

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(
        self, msg: CurrentReAddNodeMsg
    ) -> None:
        self.current_node = msg.node_data
        if (
            msg.node_data.path in self.app.cmd.paths.re_add_status_dirs
            or msg.node_data.path in self.app.cmd.paths.re_add_status_files
            or self.app.cmd.paths.has_re_add_status_paths_in(
                msg.node_data.path
            )
        ):
            self.re_add_btn.disabled = False
            self.destroy_btn.disabled = False
            self.forget_btn.disabled = False
        else:
            self.re_add_btn.disabled = True
        self.update_view_node_data(msg.node_data)
