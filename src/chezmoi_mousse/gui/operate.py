from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from chezmoi_mousse import (
    AppType,
    BindingDescription,
    Chars,
    ContainerName,
    OperateBtn,
    OperateScreenData,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    ContentsView,
    CustomHeader,
    DiffView,
    MainSectionLabel,
    OperateButtons,
    SectionLabelText,
)

from .tabs.logs_tab import OperateLog

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["OperateInfo", "OperateScreen"]


class InfoLine(StrEnum):
    add_path = "[$text-primary]The path will be added to your chezmoi dotfile manager source state.[/]"
    apply_path = "[$text-primary]The path in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_disabled = "[dim]Changes are currently disabled, running commands with '--dry-run' flag[/]"
    changes_enabled = f"[$text-warning]{Chars.warning_sign} Changes currently enabled, running commands without '--dry-run' flag.{Chars.warning_sign}[/]"
    destroy_path = "[$text-error]Permanently remove the path both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_path = "[$text-primary]Remove the path from the source state, i.e. stop managing them.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path[/]"
    )


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, *, operate_screen_data: OperateScreenData) -> None:
        super().__init__()
        self.operate_btn = operate_screen_data.operate_btn
        self.path_type = operate_screen_data.node_data.path_type
        self.operate_path = operate_screen_data.node_data.path

    def on_mount(self) -> None:
        self.write_info_lines()

    def write_info_lines(self) -> None:
        self.update("")
        lines_to_write: list[str] = []
        if self.operate_btn == OperateBtn.add_file:
            self.border_title = OperateBtn.add_file.enabled_tooltip.rstrip(".")
            lines_to_write.append(InfoLine.add_path)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.add_dir:
            self.border_title = OperateBtn.add_dir.enabled_tooltip.rstrip(".")
            lines_to_write.append(InfoLine.add_path)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.apply_path:
            self.border_title = (
                OperateBtn.apply_path.file_tooltip.rstrip(".")
                if self.path_type == "file"
                else OperateBtn.apply_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.apply_path)
            self.border_subtitle = Chars.apply_info_border
        elif self.operate_btn == OperateBtn.re_add_path:
            self.border_title = (
                OperateBtn.re_add_path.file_tooltip.rstrip(".")
                if self.path_type == "file"
                else OperateBtn.re_add_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.re_add_path)
            self.border_subtitle = Chars.re_add_info_border
        elif self.operate_btn == OperateBtn.forget_path:
            self.border_title = (
                OperateBtn.forget_path.file_tooltip.rstrip(".")
                if self.path_type == "file"
                else OperateBtn.forget_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.forget_path)
            self.border_subtitle = Chars.forget_info_border
        elif self.operate_btn == OperateBtn.destroy_path:
            self.border_title = (
                OperateBtn.destroy_path.file_tooltip.rstrip(".")
                if self.path_type == "file"
                else OperateBtn.destroy_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.destroy_path)
            self.border_subtitle = Chars.destroy_info_border
        if self.app.changes_enabled is True:
            lines_to_write.append(InfoLine.changes_enabled)
        else:
            lines_to_write.append(InfoLine.changes_disabled)
        if self.operate_btn != OperateBtn.apply_path:
            if self.git_autocommit is True:
                lines_to_write.append(InfoLine.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(InfoLine.autopush)
        # show git diff color info
        if (
            OperateBtn.apply_path == self.operate_btn
            or OperateBtn.re_add_path == self.operate_btn
        ):
            lines_to_write.append(InfoLine.diff_color)
        lines_to_write.append(
            f"[$text-primary]Operating on path: {self.operate_path}[/]"
        )
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[OperateScreenData], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="exit_operation",
            description=BindingDescription.back,
            show=True,
        )
    ]

    def __init__(
        self, *, ids: "AppIds", operate_data: "OperateScreenData"
    ) -> None:
        self.ids = ids
        super().__init__()

        self.path_arg = operate_data.node_data.path
        self.path_type = operate_data.node_data.path_type

        self.operate_btn = operate_data.operate_btn
        self.operate_btn_qid = ids.button_id("#", btn=self.operate_btn)
        self.exit_btn_id = ids.button_id(btn=OperateBtn.exit_button)
        self.exit_btn_qid = ids.button_id("#", btn=OperateBtn.exit_button)

        self.post_operate_id = ids.container_id(
            name=ContainerName.post_operate
        )
        self.post_operate_qid = ids.container_id(
            "#", name=ContainerName.post_operate
        )
        self.pre_operate_id = ids.container_id(name=ContainerName.pre_operate)
        self.pre_operate_qid = ids.container_id(
            "#", name=ContainerName.pre_operate
        )

        self.operate_data = operate_data

    def compose(self) -> ComposeResult:
        yield CustomHeader(self.ids)
        with VerticalGroup(id=self.pre_operate_id):
            yield OperateInfo(operate_screen_data=self.operate_data)
            yield MainSectionLabel(SectionLabelText.operate_context)
            if self.operate_btn == OperateBtn.apply_path:
                yield DiffView(ids=self.ids, reverse=False)
            elif self.operate_btn == OperateBtn.re_add_path:
                yield DiffView(ids=self.ids, reverse=True)
            elif self.operate_btn in (
                OperateBtn.add_file,
                OperateBtn.add_dir,
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ):
                yield ContentsView(ids=self.ids)
        with VerticalGroup(id=self.post_operate_id):
            yield MainSectionLabel(SectionLabelText.operate_output)
            yield OperateLog(ids=self.ids)
        yield OperateButtons(
            ids=self.ids, buttons=(self.operate_btn, OperateBtn.exit_button)
        )
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.configure_buttons()
        self.configure_widgets()
        self.configure_containers()

    def configure_widgets(self) -> None:
        if self.operate_btn in (OperateBtn.apply_path, OperateBtn.re_add_path):
            diff_view = self.query_exactly_one(DiffView)
            diff_view.path = self.path_arg

        elif self.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            contents_view = self.query_exactly_one(ContentsView)
            contents_view.path = self.path_arg

    def configure_buttons(self) -> None:
        op_btn = self.query_one(self.operate_btn_qid, Button)
        op_btn.disabled = False
        exit_btn = self.query_one(self.exit_btn_qid, Button)
        exit_btn.disabled = False
        exit_btn.tooltip = None

        if self.operate_btn == OperateBtn.apply_path:
            op_btn.label = OperateBtn.apply_path.label(self.path_type)
            op_btn.tooltip = OperateBtn.apply_path.tooltip(self.path_type)

        elif self.operate_btn == OperateBtn.re_add_path:
            op_btn.label = OperateBtn.re_add_path.label(self.path_type)
            op_btn.tooltip = OperateBtn.re_add_path.tooltip(self.path_type)
        elif self.operate_btn == OperateBtn.add_dir:
            op_btn.label = OperateBtn.add_dir.label(self.path_type)
            op_btn.tooltip = (
                OperateBtn.add_dir.initial_tooltip
                if self.path_type == "dir"
                else OperateBtn.add_file.initial_tooltip
            )
        elif self.operate_btn == OperateBtn.forget_path:
            op_btn.label = OperateBtn.forget_path.label(self.path_type)
            op_btn.tooltip = (
                OperateBtn.forget_path.dir_tooltip
                if self.path_type == "dir"
                else OperateBtn.forget_path.file_tooltip
            )
        elif self.operate_btn == OperateBtn.destroy_path:
            op_btn.label = OperateBtn.destroy_path.label(self.path_type)
            op_btn.tooltip = (
                OperateBtn.destroy_path.dir_tooltip
                if self.path_type == "dir"
                else OperateBtn.destroy_path.file_tooltip
            )

    def configure_containers(self) -> None:
        self.query_one(self.post_operate_qid, VerticalGroup).display = False

    def run_operate_command(self) -> "CommandResult | None":
        cmd_result: "CommandResult | None" = None
        if self.operate_btn in (OperateBtn.add_file, OperateBtn.add_dir):
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.apply_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.re_add_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.forget_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.destroy_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        else:
            self.screen.notify(
                f"Operate button not implemented: {self.operate_btn.name}",
                severity="error",
            )
        self.operate_data.command_result = cmd_result
        self.post_operate_ui_update()

    def post_operate_ui_update(self) -> None:
        pre_op_container = self.query_one(self.pre_operate_qid, VerticalGroup)
        pre_op_container.display = False
        post_op_container = self.query_one(
            self.post_operate_qid, VerticalGroup
        )
        post_op_container.display = True

        operate_button = self.query_one(self.operate_btn_qid, Button)
        operate_button.disabled = True
        operate_button.tooltip = None

        operate_exit_button = self.query_one(self.exit_btn_qid, Button)
        operate_exit_button.label = OperateBtn.exit_button.close_label

        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        if self.operate_data.command_result is not None:
            output_log.log_cmd_results(self.operate_data.command_result)
        else:
            output_log.error("Command result is None, cannot log output.")

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.exit_btn_id:
            self.dismiss(self.operate_data)
        else:
            self.run_operate_command()

    def action_exit_operation(self) -> None:
        self.dismiss(self.operate_data)
