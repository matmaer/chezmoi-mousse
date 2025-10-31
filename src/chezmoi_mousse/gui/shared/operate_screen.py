from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Label, Static

from chezmoi_mousse import (
    AppType,
    Chars,
    Id,
    OperateBtn,
    OperateScreenData,
    Tcss,
    ViewName,
    WriteCmd,
)

from .button_groups import OperateBtnHorizontal
from .contents_view import ContentsView
from .diff_view import DiffView
from .loggers import AppLog, OutputLog

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

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

    def __init__(self, operate_screen_data: OperateScreenData) -> None:
        self.operate_btn = operate_screen_data.operate_btn
        self.node_data = operate_screen_data.node_data
        super().__init__(classes=Tcss.operate_info.name)

    def on_mount(self) -> None:
        # show command help and set its subtitle
        lines_to_write: list[str] = []
        if self.operate_btn == OperateBtn.add_file:
            self.border_title = OperateBtn.add_file.enabled_tooltip.rstrip(".")
            lines_to_write.append(InfoStrings.add_path)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.add_dir:
            self.border_title = OperateBtn.add_dir.enabled_tooltip.rstrip(".")
            lines_to_write.append(InfoStrings.add_path)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.apply_path:
            self.border_title = (
                OperateBtn.apply_path.file_tooltip.rstrip(".")
                if self.node_data.path_type == "file"
                else OperateBtn.apply_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoStrings.apply_path)
            self.border_subtitle = Chars.apply_info_border
        elif self.operate_btn == OperateBtn.re_add_path:
            self.border_title = (
                OperateBtn.re_add_path.file_tooltip.rstrip(".")
                if self.node_data.path_type == "file"
                else OperateBtn.re_add_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoStrings.re_add_path)
            self.border_subtitle = Chars.re_add_info_border
        elif self.operate_btn == OperateBtn.forget_path:
            self.border_title = (
                OperateBtn.forget_path.file_tooltip.rstrip(".")
                if self.node_data.path_type == "file"
                else OperateBtn.forget_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoStrings.forget_path)
            self.border_subtitle = Chars.forget_info_border
        elif self.operate_btn == OperateBtn.destroy_path:
            self.border_title = (
                OperateBtn.destroy_path.file_tooltip.rstrip(".")
                if self.node_data.path_type == "file"
                else OperateBtn.destroy_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoStrings.destroy_path)
            self.border_subtitle = Chars.destroy_info_border

        if self.operate_btn != OperateBtn.apply_path:
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(InfoStrings.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(InfoStrings.autopush)
        # show git diff color info
        if (
            OperateBtn.apply_path == self.operate_btn
            or OperateBtn.re_add_path == self.operate_btn
        ):
            lines_to_write.append(InfoStrings.diff_color)
        lines_to_write.append(
            f"[$text-primary]Operating on path: {self.node_data.path}[/]"
        )
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[OperateScreenData], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="cancel_operation",
            description="Press the escape key to cancel",
            show=True,
        )
    ]

    def __init__(self, operate_screen_data: "OperateScreenData") -> None:
        self.ids = Id.operate_launch
        self.operate_screen_data = operate_screen_data
        super().__init__(
            id=self.ids.canvas_name, classes=Tcss.operate_screen.name
        )

    def compose(self) -> ComposeResult:
        yield OperateInfo(self.operate_screen_data)
        with Vertical():
            if self.operate_screen_data.operate_btn == OperateBtn.apply_path:
                yield DiffView(ids=self.ids, reverse=False)
            elif (
                self.operate_screen_data.operate_btn == OperateBtn.re_add_path
            ):
                yield DiffView(ids=self.ids, reverse=True)
            elif self.operate_screen_data.operate_btn in (
                OperateBtn.add_file,
                OperateBtn.add_dir,
            ):
                yield ContentsView(ids=self.ids)
            elif self.operate_screen_data.operate_btn in (
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ):
                yield DiffView(ids=self.ids, reverse=False)
            yield OperateBtnHorizontal(
                ids=self.ids,
                buttons=(
                    self.operate_screen_data.operate_btn,
                    OperateBtn.operate_cancel,
                ),
            )
        yield Footer()

    def on_mount(self) -> None:
        for button in self.screen.query(Button):
            button.disabled = False
            button.tooltip = None
        if self.operate_screen_data.operate_btn in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            diff_view = self.query_exactly_one(DiffView)
            diff_view.path = self.operate_screen_data.node_data.path
        elif self.operate_screen_data.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
        ):
            contents_view = self.query_exactly_one(ContentsView)
            contents_view.path = self.operate_screen_data.node_data.path
        elif self.operate_screen_data.operate_btn in (
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            diff_view = self.query_exactly_one(DiffView)
            diff_view.path = self.operate_screen_data.node_data.path

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.ids.button_id(
            btn=OperateBtn.operate_cancel
        ):
            self.dismiss(self.operate_screen_data)
        else:
            if self.operate_screen_data.operate_btn in (
                OperateBtn.add_file,
                OperateBtn.add_dir,
            ):
                cmd_result: "CommandResult" = self.app.chezmoi.perform(
                    WriteCmd.add,
                    path_arg=self.operate_screen_data.node_data.path,
                )
            elif self.operate_screen_data.operate_btn == OperateBtn.apply_path:
                cmd_result: "CommandResult" = self.app.chezmoi.perform(
                    WriteCmd.apply,
                    path_arg=self.operate_screen_data.node_data.path,
                )
            elif (
                self.operate_screen_data.operate_btn == OperateBtn.re_add_path
            ):
                cmd_result: "CommandResult" = self.app.chezmoi.perform(
                    WriteCmd.re_add,
                    path_arg=self.operate_screen_data.node_data.path,
                )
            elif (
                self.operate_screen_data.operate_btn == OperateBtn.forget_path
            ):
                cmd_result: "CommandResult" = self.app.chezmoi.perform(
                    WriteCmd.forget,
                    path_arg=self.operate_screen_data.node_data.path,
                )
            elif (
                self.operate_screen_data.operate_btn == OperateBtn.destroy_path
            ):
                cmd_result: "CommandResult" = self.app.chezmoi.perform(
                    WriteCmd.destroy,
                    path_arg=self.operate_screen_data.node_data.path,
                )
            else:
                self.screen.notify(
                    f"Operate button not implemented: {self.operate_screen_data.operate_btn.name}",
                    severity="error",
                )
                return None
            self.operate_screen_data.operation_executed = True

            self.app.push_screen(
                OperateResultScreen(operate_cmd_result=cmd_result),
                callback=self.handle_result_screen_dismissed,
            )

    def handle_result_screen_dismissed(
        self, result: OperateScreenData | None
    ) -> None:
        self.operate_result = result
        self.dismiss(self.operate_result)

    def action_cancel_operation(self) -> None:
        self.dismiss(self.operate_result)


class OperateResultScreen(ModalScreen[None], AppType):
    BINDINGS = [
        Binding(
            key="escape",
            action="esc_key_dismiss",
            description="Press the escape key to close",
            show=True,
        )
    ]

    def __init__(self, operate_cmd_result: "CommandResult") -> None:
        self.ids = Id.operate_result
        self.operate_cmd_result = operate_cmd_result
        super().__init__(id=self.ids.canvas_name)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Executed Commands", classes=Tcss.section_label.name)
            yield AppLog(ids=self.ids)
            yield Label(
                "Operate Command Output", classes=Tcss.section_label.name
            )
            yield OutputLog(
                ids=self.ids, view_name=ViewName.write_output_log_view
            )
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

        self.screen_app_log = self.query_one(
            self.ids.view_id("#", view=ViewName.app_log_view), AppLog
        )
        self.screen_app_log.auto_scroll = False
        self.screen_app_log.styles.height = "auto"
        self.screen_output_log = self.query_one(
            self.ids.view_id("#", view=ViewName.write_output_log_view),
            OutputLog,
        )
        self.screen_output_log.auto_scroll = False
        self.screen_app_log.log_cmd_results(self.operate_cmd_result)
        self.screen_output_log.log_cmd_results(self.operate_cmd_result)

    @on(Button.Pressed, Tcss.operate_button.value)
    def close_operate_results_screen(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.pop_screen()

    def action_esc_key_dismiss(self) -> None:
        self.app.pop_screen()
