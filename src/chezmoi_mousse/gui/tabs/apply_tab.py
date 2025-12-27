from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from chezmoi_mousse import (
    IDS,
    AppType,
    NodeData,
    OpBtnEnum,
    OpBtnLabels,
    OperateStrings,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CurrentApplyNodeMsg,
    OperateButtonMsg,
    OperateButtons,
    ViewTabButtons,
)

from .common.diff_view import DiffView
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

    def get_run_command(self, btn_enum: OpBtnEnum) -> WriteCmd:
        if self.current_node is None:
            raise ValueError("No current node selected")
        if btn_enum == OpBtnEnum.apply_path:
            return (
                WriteCmd.apply_live
                if self.app.changes_enabled
                else WriteCmd.apply_dry
            )
        elif btn_enum == OpBtnEnum.forget_path:
            return (
                WriteCmd.forget_live
                if self.app.changes_enabled
                else WriteCmd.forget_dry
            )
        elif btn_enum == OpBtnEnum.destroy_path:
            return (
                WriteCmd.destroy_live
                if self.app.changes_enabled
                else WriteCmd.destroy_dry
            )
        else:
            raise ValueError(f"Unknown button enum: {btn_enum}")

    def run_operate_command(self, btn_enum: OpBtnEnum) -> None:
        if self.current_node is None:
            return
        write_cmd: WriteCmd = self.get_run_command(btn_enum)
        operate_result = self.app.cmd.perform(
            write_cmd,
            path_arg=self.current_node.path,
            changes_enabled=self.app.changes_enabled,
        )
        self.apply_btn.disabled = True
        self.apply_btn.label = OpBtnLabels.apply_review
        if operate_result.dry_run is True:
            self.exit_btn.label = OpBtnLabels.cancel
        elif operate_result.dry_run is False:
            diff_view = self.query_exactly_one(DiffView)
            diff_view.node_data = None
            diff_view.node_data = self.current_node
            self.exit_btn.label = OpBtnLabels.reload
        self.operate_info.border_title = OperateStrings.cmd_output_subtitle
        if operate_result.exit_code == 0:
            self.operate_info.border_subtitle = OperateStrings.success_subtitle
            self.operate_info.add_class(Tcss.operate_success)
            self.operate_info.update(f"{operate_result.std_out}")
        else:
            self.operate_info.border_subtitle = OperateStrings.error_subtitle
            self.operate_info.add_class(Tcss.operate_error)
            self.operate_info.update(f"{operate_result.std_err}")

    def toggle_widget_visibility(self) -> None:
        # Widgets shown by default
        self.app.toggle_main_tabs_display()
        left_side = self.query_one(
            IDS.apply.container.left_side_q, TreeSwitcher
        )
        left_side.display = False if left_side.display is True else True
        view_switcher_buttons = self.screen.query_one(
            IDS.apply.switcher.view_buttons_q, ViewTabButtons
        )
        view_switcher_buttons.display = (
            False if view_switcher_buttons.display is True else True
        )
        self.operate_info.display = (
            True if self.operate_info.display is False else False
        )
        # Depending on self.app.operating_mode, show/hide buttons
        switch_slider = self.query_one(
            IDS.apply.container.switch_slider_q, SwitchSlider
        )
        switch_slider.display = (
            False if self.app.operating_mode is True else True
        )
        if self.app.operating_mode is True:
            self.exit_btn.display = True
            self.forget_btn.display = False
            self.destroy_btn.display = False
            switch_slider.display = False  # regardless of visibility
        else:
            self.exit_btn.display = False
            self.forget_btn.display = True
            self.destroy_btn.display = True
            # this will restore the previous vilibility, whatever it was
            switch_slider.display = True

    def write_pre_operate_info(self, btn_enum: OpBtnEnum) -> None:
        if self.current_node is None:
            return
        lines_to_write: list[str] = []
        lines_to_write.append(
            f"{OperateStrings.ready_to_run}"
            f"[$text-warning]{self.get_run_command(btn_enum).pretty_cmd} "
            f"{self.current_node.path}[/]"
        )
        self.operate_info.border_subtitle = OperateStrings.apply_subtitle
        self.operate_info.update("\n".join(lines_to_write))

    @on(CurrentApplyNodeMsg)
    def handle_new_apply_node_selected(self, msg: CurrentApplyNodeMsg) -> None:
        msg.stop()
        self.current_node = msg.node_data
        self.apply_btn.label = OpBtnLabels.apply_review
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

    @on(OperateButtonMsg)
    def handle_button_pressed(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        if msg.label == OpBtnLabels.apply_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.apply_btn.label = OpBtnLabels.apply_run
            self.write_pre_operate_info(OpBtnEnum.apply_path)
        elif msg.label == OpBtnLabels.apply_run:
            self.run_operate_command(OpBtnEnum.apply_path)
        elif msg.label == OpBtnLabels.forget_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.apply_btn.label = OpBtnLabels.forget_run
            self.write_pre_operate_info(OpBtnEnum.forget_path)
        elif msg.label == OpBtnLabels.forget_run:
            self.run_operate_command(OpBtnEnum.forget_path)
        elif msg.label == OpBtnLabels.destroy_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.apply_btn.label = OpBtnLabels.destroy_run
            self.write_pre_operate_info(OpBtnEnum.destroy_path)
        elif msg.label == OpBtnLabels.destroy_run:
            self.run_operate_command(OpBtnEnum.destroy_path)
        elif msg.label == OpBtnLabels.cancel:
            self.apply_btn.disabled = False
            self.apply_btn.label = OpBtnLabels.apply_review
            self.app.operating_mode = False
            self.toggle_widget_visibility()
        elif msg.label == OpBtnLabels.reload:
            self.app.operating_mode = False
            self.toggle_widget_visibility()
