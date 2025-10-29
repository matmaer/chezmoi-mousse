from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from chezmoi_mousse import (
    AppType,
    Chars,
    Id,
    OperateBtn,
    OperateLaunchData,
    OperateResultData,
    ReadCmd,
    Tcss,
    ViewName,
    WriteCmd,
)

from .button_groups import OperateBtnHorizontal
from .contents_view import ContentsView
from .diff_view import DiffView
from .loggers import AppLog, OutputLog

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResults, OperateLaunchData


__all__ = ["OperateInfo", "OperateScreen"]


class InfoStrings(StrEnum):
    add_path = "[$text-primary]The path will be added to your chezmoi dotfile manager source state.[/]"
    apply_path = "[$text-primary]The path in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    destroy_path = "[$text-error]Permanently remove the path both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_path = "[$text-primary]Remove the path from the source state, i.e. stop managing them.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path[/]"
    )


class OperateInfo(Static):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, operate_launch_data: OperateLaunchData) -> None:
        self.operate_btn = operate_launch_data.btn_enum_member
        self.node_data = operate_launch_data.node_data
        super().__init__(classes=Tcss.operate_info.name)

    def on_mount(self) -> None:
        # show command help and set its subtitle
        lines_to_write: list[str] = []
        if self.operate_btn == OperateBtn.add_file:
            self.border_title = OperateBtn.add_file.enabled_tooltip.rstrip(".")
            lines_to_write.append(InfoStrings.add_path.value)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.add_dir:
            self.border_title = OperateBtn.add_dir.enabled_tooltip.rstrip(".")
            lines_to_write.append(InfoStrings.add_path.value)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.apply_path:
            lines_to_write.append(InfoStrings.apply_path.value)
            self.border_subtitle = Chars.apply_info_border
        elif self.operate_btn == OperateBtn.re_add_path:
            lines_to_write.append(InfoStrings.re_add_path.value)
            self.border_subtitle = Chars.re_add_info_border
        elif self.operate_btn == OperateBtn.forget_path:
            lines_to_write.append(InfoStrings.forget_path.value)
            self.border_subtitle = Chars.forget_info_border
        elif self.operate_btn == OperateBtn.destroy_path:
            lines_to_write.append(InfoStrings.destroy_path.value)
            self.border_subtitle = Chars.destroy_info_border

        if self.operate_btn != OperateBtn.apply_path:
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(InfoStrings.auto_commit.value)
            if self.git_autopush is True:
                lines_to_write.append(InfoStrings.autopush.value)
        lines_to_write.append(
            f"[$text-primary]Operating on path: {self.node_data.path}[/]"
        )
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[OperateResultData], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="esc_key_dismiss",
            description="Press the escape key to cancel",
            show=True,
        )
    ]

    def __init__(self, launch_data: "OperateLaunchData") -> None:
        self.ids = Id.operate_launch
        self.launch_data = launch_data
        self.operate_btn = launch_data.btn_enum_member
        super().__init__(
            id=self.ids.canvas_name, classes=Tcss.operate_screen.name
        )
        self.operate_result = OperateResultData(
            path=self.launch_data.node_data.path
        )

    def compose(self) -> ComposeResult:
        assert self.operate_btn is not None
        yield OperateInfo(self.launch_data)
        if self.launch_data.btn_enum_member == OperateBtn.apply_path:
            yield DiffView(ids=self.ids, reverse=False)
        elif self.launch_data.btn_enum_member == OperateBtn.re_add_path:
            yield DiffView(ids=self.ids, reverse=True)
        elif self.launch_data.btn_enum_member in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            yield ContentsView(ids=self.ids)
        yield OperateBtnHorizontal(
            ids=self.ids, buttons=(self.operate_btn, OperateBtn.operate_cancel)
        )
        yield Footer()

    def on_mount(self) -> None:
        for button in self.screen.query(Button):
            button.disabled = False
            button.tooltip = None
        if self.launch_data.btn_enum_member in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            diff_view = self.query_exactly_one(DiffView)
            diff_view.path = self.launch_data.node_data.path
            diff_view.border_title = str(self.launch_data.node_data.path)
        elif self.launch_data.btn_enum_member in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            contents_view = self.query_exactly_one(ContentsView)
            contents_view.path = self.launch_data.node_data.path
            contents_view.border_title = str(self.launch_data.node_data.path)

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.ids.button_id(
            btn=OperateBtn.operate_cancel
        ):
            self.dismiss(self.operate_result)
        else:
            self.app.push_screen(
                OperateResultScreen(launch_data=self.launch_data),
                callback=self.handle_result_screen_dismissed,
            )

    def handle_result_screen_dismissed(
        self, result: OperateResultData | None
    ) -> None:
        self.operate_result = result
        self.dismiss(self.operate_result)

    def action_esc_key_dismiss(self) -> None:
        self.dismiss(self.operate_result)


class OperateResultScreen(Screen[OperateResultData], AppType):
    BINDINGS = [
        Binding(
            key="escape",
            action="esc_key_dismiss",
            description="Press the escape key to close",
            show=True,
        )
    ]

    def __init__(self, launch_data: "OperateLaunchData") -> None:
        self.ids = Id.operate_result
        self.launch_data = launch_data
        self.cmd_result: "CommandResults | None" = None
        self.operate_result = OperateResultData(
            path=self.launch_data.node_data.path
        )
        super().__init__(id=self.ids.canvas_name)

    def compose(self) -> ComposeResult:
        yield Label("Executed Commands", classes=Tcss.section_label.name)
        yield AppLog(ids=self.ids)
        yield Label("Operate Command Output", classes=Tcss.section_label.name)
        yield OutputLog(ids=self.ids, view_name=ViewName.write_output_log_view)
        yield OperateBtnHorizontal(
            ids=self.ids, buttons=(OperateBtn.operate_close,)
        )
        yield Footer()

    def on_mount(self) -> None:
        button = self.query_one(
            self.ids.button_id("#", btn=OperateBtn.operate_close)
        )
        button.disabled = False
        button.tooltip = None

        app_log = self.query_one(AppLog)
        app_log.auto_scroll = False
        app_log.styles.height = "auto"
        output_log = self.query_one(OutputLog)
        output_log.auto_scroll = False

        if self.launch_data.btn_enum_member == OperateBtn.add_file:
            self.cmd_result = self.app.chezmoi.perform(
                WriteCmd.add, path_arg=self.launch_data.node_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.apply_path:
            self.cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply, path_arg=self.launch_data.node_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.re_add_path:
            self.cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add, path_arg=self.launch_data.node_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.forget_path:
            self.cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget, path_arg=self.launch_data.node_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.destroy_path:
            self.cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy, path_arg=self.launch_data.node_data.path
            )
        self.operate_result.operation_executed = True
        self.operate_result.command_results = self.cmd_result
        if self.cmd_result is None:
            app_log.write("No command result to log.")
            output_log.write("No command result to log.")
            return

        app_log.log_cmd_results(self.cmd_result)
        output_log.log_cmd_results(self.cmd_result)

        # Refresh chezmoi status and managed data
        managed_dirs: "CommandResults" = self.app.chezmoi.read(
            ReadCmd.managed_dirs
        )
        app_log.log_cmd_results(managed_dirs)

        managed_files: "CommandResults" = self.app.chezmoi.read(
            ReadCmd.managed_files
        )
        app_log.log_cmd_results(managed_files)

        status_files: "CommandResults" = self.app.chezmoi.read(
            ReadCmd.status_files
        )
        app_log.log_cmd_results(status_files)

        status_dirs: "CommandResults" = self.app.chezmoi.read(
            ReadCmd.status_dirs
        )
        app_log.log_cmd_results(status_dirs)

        self.app.chezmoi.clear_cache()
        app_log.info("Cleared managed paths cache.")

    @on(Button.Pressed, Tcss.operate_button.value)
    def close_operate_results_screen(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(self.operate_result)

    def action_esc_key_dismiss(self) -> None:
        self.dismiss(self.operate_result)
