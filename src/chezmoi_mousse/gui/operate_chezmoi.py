from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Label

from chezmoi_mousse import (
    IDS_OPERATE_CHEZMOI,
    AppType,
    BindingAction,
    BindingDescription,
    OperateBtn,
    SectionLabels,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    ContentsView,
    CustomHeader,
    DebugLog,
    DiffView,
    OperateButtons,
    OperateInfo,
    OperateLog,
)

__all__ = ["OperateChezmoi"]


class OperateChezmoi(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action=BindingAction.exit_screen,
            description=BindingDescription.cancel,
        )
    ]

    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.op_data = self.app.operate_data
        self.reverse = (
            False if self.op_data.btn_enum == OperateBtn.apply_path else True
        )
        self.ids = IDS_OPERATE_CHEZMOI

    def compose(self) -> ComposeResult:
        yield CustomHeader(self.ids)
        yield OperateInfo(self.ids)
        yield VerticalGroup(id=self.ids.container.pre_operate)
        with VerticalGroup(id=self.ids.container.post_operate):
            yield Label(
                SectionLabels.operate_output, classes=Tcss.main_section_label
            )
            yield OperateLog(ids=self.ids)
        if self.app.dev_mode:
            yield Label(SectionLabels.debug_log_output)
            yield DebugLog(self.ids)
        yield OperateButtons(
            ids=self.ids,
            buttons=(self.op_data.btn_enum, OperateBtn.operate_exit),
        )
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.post_op_container = self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        )
        self.post_op_container.display = False
        self.pre_op_container = self.query_one(
            self.ids.container.pre_operate_q, VerticalGroup
        )
        self.op_btn = self.query_one(
            self.ids.operate_button_id("#", btn=self.op_data.btn_enum), Button
        )
        self.op_btn.label = self.op_data.btn_label
        self.op_btn.tooltip = self.op_data.btn_tooltip
        self.exit_btn = self.query_one(
            self.ids.operate_button_id("#", btn=OperateBtn.operate_exit),
            Button,
        )
        if self.op_data.btn_enum in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            self.pre_op_container.mount(
                DiffView(ids=self.ids, reverse=self.reverse)
            )
            diff_view = self.pre_op_container.query_one(
                self.ids.container.diff_q, DiffView
            )
            diff_view.on_mount()
            diff_view.node_data = self.op_data.node_data
            diff_view.remove_class(Tcss.border_title_top)
        else:
            self.pre_op_container.mount(ContentsView(ids=self.ids))
            contents_view = self.pre_op_container.query_one(
                self.ids.container.contents_q, ContentsView
            )
            contents_view.node_data = self.op_data.node_data
            contents_view.remove_class(Tcss.border_title_top)

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OperateBtn.operate_exit.cancel_label:
            self.app.operate_cmd_result = None
            self.dismiss()
        elif event.button.label == OperateBtn.operate_exit.reload_label:
            self.dismiss()
        else:
            self.run_operate_command()

    def run_operate_command(self) -> None:
        if self.op_data.node_data is None:
            raise ValueError(
                "self.op_data.node_data is None in operate command"
            )
        if self.op_data.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=self.op_data.node_data.path,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.apply_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=self.op_data.node_data.path,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.re_add_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=self.op_data.node_data.path,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.forget_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=self.op_data.node_data.path,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.destroy_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=self.op_data.node_data.path,
                changes_enabled=self.app.changes_enabled,
            )
        else:
            raise ValueError(
                "self.app.operate_cmd_result is None after running command"
            )
        self.pre_op_container.display = False
        self.post_op_container.display = True
        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        output_log.log_cmd_results(self.app.operate_cmd_result)
        if self.app.changes_enabled is False:
            self.op_btn.disabled = True
            self.op_btn.tooltip = None
            self.exit_btn.label = OperateBtn.operate_exit.reload_label
            new_description = BindingDescription.reload
            self.app.update_binding_description(
                BindingAction.exit_screen, new_description
            )

    def action_exit_screen(self) -> None:
        self.screen.dismiss()
