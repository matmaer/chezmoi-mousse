from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from chezmoi_mousse import IDS, AppType, NodeData, Tcss
from chezmoi_mousse.shared import CurrentApplyNodeMsg, OperateButtons

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_base import TabsBase

__all__ = ["ApplyTab"]


class ApplyTab(TabsBase, AppType):

    def __init__(self) -> None:
        super().__init__(ids=IDS.apply)
        self.current_node: "NodeData | None" = None

    def compose(self) -> ComposeResult:
        yield Static(
            id=IDS.apply.static.operate_info, classes=Tcss.operate_info
        )
        with Horizontal():
            yield TreeSwitcher(IDS.apply)
            yield ViewSwitcher(ids=IDS.apply)
        yield SwitchSlider(ids=IDS.apply)
        yield OperateButtons(ids=IDS.apply)

    def on_mount(self) -> None:
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
        self.exit_btn = self.query_one(
            IDS.apply.operate_btn.operate_exit_q, Button
        )
        self.operate_info = self.query_one(
            IDS.apply.static.operate_info_q, Static
        )
        self.operate_info.display = False

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        self.current_node = msg.node_data
        if (
            msg.node_data.path in self.app.cmd.paths.status_dirs
            or msg.node_data.path in self.app.cmd.paths.apply_status_files
            or self.app.cmd.paths.has_apply_status_paths_in(msg.node_data.path)
        ):
            self.apply_btn.disabled = False
            self.destroy_btn.disabled = False
            self.forget_btn.disabled = False
        else:
            self.apply_btn.disabled = True
        self.update_view_node_data(msg.node_data)
