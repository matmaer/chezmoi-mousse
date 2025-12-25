from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from chezmoi_mousse import (
    IDS,
    AppType,
    NodeData,
    OpBtnLabels,
    OperateStrings,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CurrentReAddNodeMsg,
    OperateButtonMsg,
    OperateButtons,
    ViewTabButtons,
)

from .common.diff_view import DiffView
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
        self.exit_btn = self.query_one(
            IDS.re_add.operate_btn.operate_exit_q, Button
        )
        self.re_add_btn = self.query_one(
            IDS.re_add.operate_btn.re_add_path_q, Button
        )
        self.operate_info = self.query_one(
            IDS.re_add.static.operate_info_q, Static
        )
        self.operate_info.display = False

    def get_run_command(self, btn_label: OpBtnLabels) -> WriteCmd:
        if self.current_node is None:
            raise ValueError("No current node selected")
        if btn_label in (OpBtnLabels.re_add_run, OpBtnLabels.re_add_review):
            return (
                WriteCmd.re_add_live
                if self.app.changes_enabled
                else WriteCmd.re_add_dry
            )
        elif btn_label in (OpBtnLabels.forget_run, OpBtnLabels.forget_review):
            return (
                WriteCmd.forget_live
                if self.app.changes_enabled
                else WriteCmd.forget_dry
            )
        elif btn_label in (
            OpBtnLabels.destroy_run,
            OpBtnLabels.destroy_review,
        ):
            return (
                WriteCmd.destroy_live
                if self.app.changes_enabled
                else WriteCmd.destroy_dry
            )
        else:
            raise ValueError(f"Unknown button label: {btn_label}")

    def run_operate_command(self, btn_label: OpBtnLabels) -> None:
        if self.current_node is None:
            return
        write_cmd: WriteCmd = self.get_run_command(btn_label)
        operate_result = self.app.chezmoi.perform(
            write_cmd,
            path_arg=self.current_node.path,
            changes_enabled=self.app.changes_enabled,
        )
        self.re_add_btn.disabled = True
        self.re_add_btn.label = OpBtnLabels.re_add_review
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
            IDS.re_add.container.left_side_q, TreeSwitcher
        )
        left_side.display = False if left_side.display is True else True
        view_switcher_buttons = self.screen.query_one(
            IDS.re_add.switcher.view_buttons_q, ViewTabButtons
        )
        view_switcher_buttons.display = (
            False if view_switcher_buttons.display is True else True
        )
        self.operate_info.display = (
            True if self.operate_info.display is False else False
        )
        # Depending on self.app.operating_mode, show/hide buttons
        switch_slider = self.query_one(
            IDS.re_add.container.switch_slider_q, SwitchSlider
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

    def write_pre_operate_info(self, btn_label: OpBtnLabels) -> None:
        if self.current_node is None:
            return
        lines_to_write: list[str] = []
        lines_to_write.append(
            f"{OperateStrings.ready_to_run}"
            f"[$text-warning]{self.get_run_command(btn_label).pretty_cmd} "
            f"{self.current_node.path}[/]"
        )
        if self.app.changes_enabled is True:
            if self.git_autocommit is True:
                lines_to_write.append(OperateStrings.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(OperateStrings.auto_push)
        lines_to_write.append(OperateStrings.diff_color)
        self.operate_info.border_subtitle = OperateStrings.re_add_subtitle
        self.operate_info.update("\n".join(lines_to_write))

    @on(CurrentReAddNodeMsg)
    def handle_new_re_add_node_selected(
        self, msg: CurrentReAddNodeMsg
    ) -> None:
        msg.stop()
        self.current_node = msg.node_data
        self.re_add_btn.label = OpBtnLabels.re_add_review
        if (
            msg.node_data.path in self.app.chezmoi.status_dirs
            or msg.node_data.path in self.app.chezmoi.re_add_status_files
            or self.app.chezmoi.has_re_add_status_paths_in(msg.node_data.path)
        ):
            self.re_add_btn.disabled = False
            self.destroy_btn.disabled = False
            self.forget_btn.disabled = False
        else:
            self.re_add_btn.disabled = True
        self.update_view_node_data(msg.node_data)

    @on(OperateButtonMsg)
    def handle_button_pressed(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        if msg.label == OpBtnLabels.re_add_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.re_add_btn.label = OpBtnLabels.re_add_run
            self.write_pre_operate_info(OpBtnLabels.re_add_run)
        elif msg.label == OpBtnLabels.re_add_run:
            self.run_operate_command(OpBtnLabels.re_add_run)
        elif msg.label == OpBtnLabels.destroy_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.re_add_btn.label = OpBtnLabels.destroy_run
            self.write_pre_operate_info(OpBtnLabels.destroy_run)
        elif msg.label == OpBtnLabels.destroy_run:
            self.run_operate_command(OpBtnLabels.destroy_run)
        elif msg.label == OpBtnLabels.forget_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.re_add_btn.label = OpBtnLabels.forget_run
            self.write_pre_operate_info(OpBtnLabels.forget_run)
        elif msg.label == OpBtnLabels.forget_run:
            self.run_operate_command(OpBtnLabels.forget_run)
        elif msg.label == OpBtnLabels.cancel:
            self.app.operating_mode = False
            self.re_add_btn.disabled = False
            self.re_add_btn.label = OpBtnLabels.re_add_review
            self.toggle_widget_visibility()
        elif msg.label == OpBtnLabels.reload:
            self.app.operating_mode = False
            self.toggle_widget_visibility()
