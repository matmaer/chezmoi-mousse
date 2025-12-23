from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from chezmoi_mousse import (
    IDS,
    AppType,
    NodeData,
    OpBtnLabels,
    OpBtnToolTips,
    OperateStrings,
    PathKind,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    CurrentReAddNodeMsg,
    DiffView,
    OperateButtonMsg,
    OperateButtons,
    ViewTabButtons,
)

from .common.switch_slider import SwitchSlider
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.tabs_container import TabsBase

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

    def get_command(self) -> WriteCmd:
        if self.current_node is None:
            raise ValueError("No current node selected")
        if self.current_node.path_kind == PathKind.FILE:
            return (
                WriteCmd.re_add_file_live
                if self.app.changes_enabled
                else WriteCmd.re_add_file_dry
            )
        elif self.current_node.path_kind == PathKind.DIR:
            return (
                WriteCmd.re_add_dir_live
                if self.app.changes_enabled
                else WriteCmd.re_add_dir_dry
            )
        else:
            raise ValueError("Invalid path kind for re-add operation")

    def run_operate_command(self) -> None:
        if self.current_node is None:
            return
        write_cmd: WriteCmd = self.get_command()
        operate_result = self.app.chezmoi.perform(
            write_cmd,
            path_arg=self.current_node.path,
            changes_enabled=self.app.changes_enabled,
        )
        self.re_add_btn.disabled = True
        self.re_add_btn.tooltip = None
        self.re_add_btn.label = OpBtnLabels.re_add_review
        if operate_result.dry_run is True:
            self.exit_btn.label = OpBtnLabels.cancel
        elif operate_result.dry_run is False:
            self.app.chezmoi.update_managed_paths()
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

    def write_pre_operate_info(self) -> None:
        if self.current_node is None:
            return
        lines_to_write: list[str] = []
        lines_to_write.append(
            f"[$text-warning]Ready to run [/]"
            f"[$warning]{self.get_command().pretty_cmd} "
            f"{self.current_node.path}[/]"
        )
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateStrings.changes_enabled)
            if self.git_autocommit is True:
                lines_to_write.append(OperateStrings.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(OperateStrings.auto_push)
        else:
            lines_to_write.append(OperateStrings.changes_disabled)
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
            or self.app.chezmoi.re_add_status_files_in(msg.node_data.path)
        ):
            self.re_add_btn.disabled = False
            self.re_add_btn.tooltip = OpBtnToolTips.review
        else:
            self.re_add_btn.disabled = True
            self.re_add_btn.tooltip = OpBtnToolTips.path_no_status
        self.update_other_buttons(msg.node_data)
        self.update_view_node_data(msg.node_data)

    @on(OperateButtonMsg)
    def handle_button_pressed(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        if msg.label == OpBtnLabels.re_add_review:
            self.app.operating_mode = True
            self.toggle_widget_visibility()
            self.re_add_btn.label = OpBtnLabels.re_add_run
            self.re_add_btn.tooltip = self.get_command().pretty_cmd
            self.write_pre_operate_info()
        elif msg.label == OpBtnLabels.re_add_run:
            self.run_operate_command()
        elif msg.label == OpBtnLabels.cancel:
            self.app.operating_mode = False
            self.re_add_btn.disabled = False
            self.re_add_btn.label = OpBtnLabels.re_add_review
            self.re_add_btn.tooltip = OpBtnToolTips.review
            self.toggle_widget_visibility()
        elif msg.label == OpBtnLabels.reload:
            self.app.operating_mode = False
            self.toggle_widget_visibility()
