from enum import StrEnum
from subprocess import CompletedProcess

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.screen import Screen
from textual.widgets import Button, Static

from chezmoi_mousse import (
    AppType,
    Canvas,
    ChangeCmd,
    Chars,
    Id,
    OperateBtn,
    OperateLaunchData,
    OperateResultData,
    Tcss,
)
from chezmoi_mousse.gui.shared.button_groups import OperateBtnHorizontal

from .contents_view import ContentsView
from .diff_view import DiffView

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

    def __init__(self, *, operate_btn: OperateBtn) -> None:
        self.operate_btn = operate_btn
        super().__init__(classes=Tcss.operate_info.name)

    def on_mount(self) -> None:
        lines_to_write: list[str] = []

        # show command help and set the subtitle
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
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[OperateResultData], AppType):

    BINDINGS = [Binding(key="escape", action="esc_key_dismiss", show=True)]

    def __init__(self, operate_launch_data: OperateLaunchData) -> None:
        self.ids = Id.operate_screen
        self.path = operate_launch_data.path
        self.btn_enum_member = operate_launch_data.btn_enum_member
        self.button_id = operate_launch_data.button_id

        super().__init__(
            id=Canvas.operate.name, classes=Tcss.operate_screen.name
        )
        self.operate_result = OperateResultData(path=self.path)

    def compose(self) -> ComposeResult:
        yield OperateInfo(operate_btn=self.btn_enum_member)
        if self.btn_enum_member == OperateBtn.apply_file:
            yield DiffView(ids=self.ids, reverse=False)
        elif self.btn_enum_member == OperateBtn.re_add_file:
            yield DiffView(ids=self.ids, reverse=True)
        elif self.btn_enum_member == OperateBtn.add_file:
            yield ContentsView(ids=self.ids)
        yield OperateBtnHorizontal(
            ids=self.ids,
            buttons=(self.btn_enum_member, OperateBtn.operate_dismiss),
        )

    def on_mount(self) -> None:
        if self.btn_enum_member in (
            OperateBtn.apply_file,
            OperateBtn.re_add_file,
        ):
            diff_view = self.query_one(DiffView)
            diff_view.path = self.path
        elif self.btn_enum_member == OperateBtn.add_file:
            contents_view = self.query_one(ContentsView)
            contents_view.path = self.path

    def run_change_command(self) -> CompletedProcess[str]:
        if self.btn_enum_member == OperateBtn.apply_file:
            result: CompletedProcess[str] = self.app.chezmoi.perform(
                ChangeCmd.apply, change_arg=str(self.path)
            )
        elif self.btn_enum_member == OperateBtn.re_add_file:
            result: CompletedProcess[str] = self.app.chezmoi.perform(
                ChangeCmd.re_add, change_arg=str(self.path)
            )
        elif self.btn_enum_member == OperateBtn.add_file:
            result: CompletedProcess[str] = self.app.chezmoi.perform(
                ChangeCmd.add, change_arg=str(self.path)
            )
        elif self.btn_enum_member == OperateBtn.forget_file:
            result: CompletedProcess[str] = self.app.chezmoi.perform(
                ChangeCmd.forget, change_arg=str(self.path)
            )
        else:
            result: CompletedProcess[str] = self.app.chezmoi.perform(
                ChangeCmd.destroy, change_arg=str(self.path)
            )
        self.operate_result.operation_executed = True
        self.operate_result.completed_process_data = result
        return result

    def action_esc_key_dismiss(self) -> None:
        self.dismiss(self.operate_result)

    def on_click(self, event: Click) -> None:
        if event.chain == 2:
            self.dismiss(self.operate_result)

    @on(Button.Pressed)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == self.ids.button_id(
            btn=OperateBtn.operate_dismiss
        ):
            self.dismiss(self.operate_result)
        elif event.button.id == self.ids.button_id(btn=OperateBtn.apply_file):
            self.notify(f"Applied changes to {self.path}")
        elif event.button.id == self.ids.button_id(btn=OperateBtn.re_add_file):
            self.notify(f"Re-added {self.path} to source state")
        elif event.button.id == self.ids.button_id(btn=OperateBtn.add_file):
            self.app.chezmoi.perform(ChangeCmd.add, change_arg=str(self.path))
            self.notify(f"Added {self.path} to source state")
        elif event.button.id == self.ids.button_id(btn=OperateBtn.forget_file):
            self.notify(f"Forgot {self.path} from source state")
        elif event.button.id == self.ids.button_id(
            btn=OperateBtn.destroy_file
        ):
            self.notify(f"Destroyed {self.path} from source state and disk")
        elif event.button.id == self.ids.button_id(btn=OperateBtn.add_dir):
            self.notify(f"Added directory {self.path} to source state")
        else:
            self.notify("Unhandled operate button pressed", severity="error")

        # cmd_result: CompletedProcess[str] = self.run_change_command()
