from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from chezmoi_mousse import (
    AppType,
    ChangeCmd,
    Chars,
    Id,
    OperateBtn,
    OperateResultData,
    Tcss,
)
from chezmoi_mousse.gui.shared.button_groups import OperateBtnHorizontal

from .contents_view import ContentsView
from .diff_view import DiffView
from .loggers import AppLog, OutputLog

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResults, OperateLaunchData


__all__ = ["OperateInfo", "OperateScreen"]


class InfoStrings(StrEnum):
    add_file = "[$text-primary]Path will be added to your chezmoi dotfile manager source state.[/]"
    apply_file = "[$text-primary]The file in the destination directory will be modified.[/]"
    # apply_dir = "[$text-primary]The directory in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    destroy_file = "[$text-error]Permanently remove the file both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    # destroy_dir = "[$text-error]Permanently remove the directory both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_file = "[$text-primary]Remove the file from the source state, i.e. stop managing them.[/]"
    # forget_dir = "[$text-primary]Remove the directory from the source state, i.e. stop managing them.[/]"
    re_add_file = (
        "[$text-primary]Overwrite the source state with current local file[/]"
    )
    # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(
        self, *, operate_btn: OperateBtn, operate_path: Path | list[Path]
    ) -> None:
        self.operate_btn = operate_btn
        self.operate_path = operate_path
        super().__init__(classes=Tcss.operate_info.name)

    def on_mount(self) -> None:
        self.border_subtitle = "escape to cancel"
        lines_to_write: list[str] = []
        # show command help and set its subtitle
        if OperateBtn.apply_file == self.operate_btn:
            lines_to_write.append(InfoStrings.apply_file.value)
            self.border_subtitle = Chars.apply_file_info_border
        elif OperateBtn.re_add_file == self.operate_btn:
            lines_to_write.append(InfoStrings.re_add_file.value)
            self.border_subtitle = Chars.re_add_file_info_border
        elif OperateBtn.add_file == self.operate_btn:
            lines_to_write.append(InfoStrings.add_file.value)
            self.border_subtitle = Chars.add_file_info_border
        elif OperateBtn.forget_file == self.operate_btn:
            lines_to_write.append(InfoStrings.forget_file.value)
            self.border_subtitle = Chars.forget_file_info_border
        elif OperateBtn.destroy_file == self.operate_btn:
            lines_to_write.append(InfoStrings.destroy_file.value)
            self.border_subtitle = Chars.destroy_file_info_border
        # show git auto warnings
        if not OperateBtn.apply_file == self.operate_btn:
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(InfoStrings.auto_commit.value)
            if self.git_autopush is True:
                lines_to_write.append(InfoStrings.autopush.value)
        # show git diff color info
        if (
            OperateBtn.apply_file == self.operate_btn
            or OperateBtn.re_add_file == self.operate_btn
        ):
            lines_to_write.append(InfoStrings.diff_color.value)
        lines_to_write.append(
            f"[$text-primary]Operating on path: {self.operate_path}[/]"
        )
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[OperateResultData], AppType):

    BINDINGS = [Binding(key="escape", action="esc_key_dismiss", show=True)]

    def __init__(self, launch_data: "OperateLaunchData") -> None:
        self.ids = Id.operate_launch_screen
        self.launch_data = launch_data
        super().__init__(
            id=self.ids.canvas_name, classes=Tcss.operate_screen.name
        )
        self.operate_result = OperateResultData(path=self.launch_data.path)

    def compose(self) -> ComposeResult:
        yield OperateInfo(
            operate_btn=self.launch_data.btn_enum_member,
            operate_path=self.launch_data.path,
        )
        if self.launch_data.btn_enum_member == OperateBtn.apply_file:
            yield DiffView(ids=self.ids, reverse=False)
        elif self.launch_data.btn_enum_member == OperateBtn.re_add_file:
            yield DiffView(ids=self.ids, reverse=True)
        elif self.launch_data.btn_enum_member == OperateBtn.add_file:
            yield ContentsView(ids=self.ids)
        yield OperateBtnHorizontal(
            ids=self.ids,
            buttons=(
                self.launch_data.btn_enum_member,
                OperateBtn.operate_dismiss,
            ),
        )

    def on_mount(self) -> None:
        if self.launch_data.btn_enum_member in (
            OperateBtn.apply_file,
            OperateBtn.re_add_file,
        ):
            diff_view = self.query_one(DiffView)
            diff_view.path = self.launch_data.path
        elif self.launch_data.btn_enum_member == OperateBtn.add_file:
            contents_view = self.query_one(ContentsView)
            contents_view.path = self.launch_data.path

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.ids.button_id(
            btn=OperateBtn.operate_dismiss
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
        if result is None:
            self.notify(
                "Operate result screen dismissed without result.",
                severity="error",
            )
        self.operate_result = result
        self.dismiss(self.operate_result)

    def action_esc_key_dismiss(self) -> None:
        self.dismiss(self.operate_result)

    def on_click(self, event: Click) -> None:
        if event.chain == 2:
            self.dismiss(self.operate_result)


class OperateResultScreen(Screen[OperateResultData], AppType):

    def __init__(self, launch_data: "OperateLaunchData") -> None:
        self.ids = Id.operate_result_screen
        self.launch_data = launch_data
        self.cmd_result: "CommandResults | None" = None
        self.operate_result = OperateResultData(path=self.launch_data.path)
        super().__init__(id=self.ids.canvas_name)

    def compose(self) -> ComposeResult:
        yield Label("Executed Commands", classes=Tcss.section_label.name)
        yield AppLog(ids=self.ids)
        yield Label("Operate Command Output", classes=Tcss.section_label.name)
        yield OutputLog(ids=self.ids)
        yield OperateBtnHorizontal(
            ids=self.ids, buttons=(OperateBtn.close_operate_results,)
        )

    def on_mount(self) -> None:
        app_log = self.query_one(AppLog)
        output_log = self.query_one(OutputLog)
        if self.launch_data.btn_enum_member == OperateBtn.apply_file:
            self.cmd_result = self.app.chezmoi.perform(
                ChangeCmd.apply, path_arg=self.launch_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.re_add_file:
            self.cmd_result = self.app.chezmoi.perform(
                ChangeCmd.re_add, path_arg=self.launch_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.add_file:
            self.cmd_result = self.app.chezmoi.perform(
                ChangeCmd.add, path_arg=self.launch_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.forget_file:
            self.cmd_result = self.app.chezmoi.perform(
                ChangeCmd.forget, path_arg=self.launch_data.path
            )
        elif self.launch_data.btn_enum_member == OperateBtn.destroy_file:
            self.cmd_result = self.app.chezmoi.perform(
                ChangeCmd.destroy, path_arg=self.launch_data.path
            )
        self.operate_result.operation_executed = True
        self.operate_result.command_results = self.cmd_result
        if self.cmd_result is None:
            app_log.write("No command result to log.")
            output_log.write("No command result to log.")
            return
        app_log.log_cmd_results(self.cmd_result)
        output_log.log_cmd_results(self.cmd_result)

    @on(Button.Pressed, Tcss.operate_button.value)
    def close_operate_results_screen(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(self.operate_result)
