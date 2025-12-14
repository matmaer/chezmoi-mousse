from textual import on
from textual.widgets import Button

from chezmoi_mousse import IDS, AppType, OperateBtn, Tcss, WriteCmd
from chezmoi_mousse.shared import ContentsView, DiffView, OperateScreenBase

__all__ = ["OperateChezmoi"]


class OperateChezmoi(OperateScreenBase, AppType):

    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.reverse = (
            False if self.op_data.btn_enum == OperateBtn.apply_path else True
        )
        self.repo_arg: str | None = None

    def on_mount(self) -> None:
        super().on_mount()
        if self.op_data.btn_enum in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            self.pre_op_container.mount(
                DiffView(ids=IDS.operate, reverse=self.reverse)
            )
            diff_view = self.pre_op_container.query_one(
                IDS.operate.container.diff_q, DiffView
            )
            diff_view.node_data = self.op_data.node_data
            diff_view.remove_class(Tcss.border_title_top)
        else:
            self.pre_op_container.mount(ContentsView(ids=IDS.operate))
            contents_view = self.pre_op_container.query_one(
                IDS.operate.container.contents_q, ContentsView
            )
            contents_view.node_data = self.op_data.node_data
            contents_view.remove_class(Tcss.border_title_top)

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label in (
            OperateBtn.add_dir.dir_label,
            OperateBtn.add_file.file_label,
            OperateBtn.apply_path.dir_label,
            OperateBtn.apply_path.file_label,
            OperateBtn.destroy_path.dir_label,
            OperateBtn.destroy_path.file_label,
            OperateBtn.forget_path.dir_label,
            OperateBtn.forget_path.file_label,
            OperateBtn.re_add_path.dir_label,
            OperateBtn.re_add_path.file_label,
        ):
            self.run_operate_command()
        if event.button.label == OperateBtn.operate_exit.cancel_label:
            self.app.operate_cmd_result = None
            self.dismiss()
        elif event.button.label == OperateBtn.operate_exit.reload_label:
            self.dismiss()

    def run_operate_command(self) -> None:
        if self.op_data.node_data is not None:
            path_arg = self.op_data.node_data.path
        else:
            path_arg = None
        if self.op_data.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.apply_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.re_add_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.forget_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.destroy_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        if self.app.operate_cmd_result is None:
            raise ValueError(
                "self.app.operate_cmd_result is None after running command"
            )
        self.pre_op_container.display = False
        self.post_op_container.display = True
        self.write_to_output_log()
        if self.app.operate_cmd_result.dry_run is True:
            return
        self.update_buttons()
        self.update_key_binding()
