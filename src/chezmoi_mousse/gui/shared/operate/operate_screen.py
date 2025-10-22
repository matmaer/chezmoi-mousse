from enum import StrEnum

from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import Click
from textual.screen import Screen
from textual.widgets import RichLog, Static

from chezmoi_mousse import (
    AppType,
    Canvas,
    Chars,
    Id,
    OperateBtn,
    OperateLaunchData,
    OperateResultData,
    Tcss,
)

__all__ = ["OperateInfo", "OperateScreen"]


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    class Strings(StrEnum):
        container_id = "operate_help"
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
        re_add_file = "[$text-primary]Overwrite the source state with current local file[/]"
        # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"

    def __init__(self, *, button_id: str) -> None:
        self.button_id = button_id
        super().__init__(
            id=OperateInfo.Strings.container_id, classes=Tcss.operate_info.name
        )

    def on_mount(self) -> None:
        lines_to_write: list[str] = []

        # show command help and set the subtitle
        if self.button_id == Id.apply_tab.button_id(btn=OperateBtn.apply_file):
            lines_to_write.append(OperateInfo.Strings.apply_file.value)
            self.border_subtitle = Chars.apply_file_info_border
        elif self.button_id == Id.re_add_tab.button_id(
            btn=OperateBtn.re_add_file
        ):
            lines_to_write.append(OperateInfo.Strings.re_add_file.value)
            self.border_subtitle = Chars.re_add_file_info_border
        elif self.button_id in (
            Id.add_tab.button_id(btn=OperateBtn.add_dir),
            Id.add_tab.button_id(btn=OperateBtn.add_file),
        ):
            lines_to_write.append(OperateInfo.Strings.add_file.value)
            self.border_subtitle = Chars.add_file_info_border
        elif self.button_id in (
            Id.apply_tab.button_id(btn=OperateBtn.forget_file),
            Id.re_add_tab.button_id(btn=OperateBtn.forget_file),
        ):
            lines_to_write.append(OperateInfo.Strings.forget_file.value)
            self.border_subtitle = Chars.forget_file_info_border
        elif self.button_id in (
            Id.apply_tab.button_id(btn=OperateBtn.destroy_file),
            Id.re_add_tab.button_id(btn=OperateBtn.destroy_file),
        ):
            lines_to_write.append(OperateInfo.Strings.destroy_file.value)
            self.border_subtitle = Chars.destroy_file_info_border

        # show git auto warnings
        if not self.button_id == (
            Id.apply_tab.button_id(btn=OperateBtn.apply_file)
        ):
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(OperateInfo.Strings.auto_commit.value)
            if self.git_autopush is True:
                lines_to_write.append(OperateInfo.Strings.autopush.value)

        # show git diff color info
        if self.button_id in (
            Id.apply_tab.button_id(btn=OperateBtn.apply_file),
            Id.re_add_tab.button_id(btn=OperateBtn.re_add_file),
        ):
            lines_to_write.append(OperateInfo.Strings.diff_color.value)

        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[OperateResultData], AppType):

    BINDINGS = [Binding(key="escape", action="cancel_operation", show=True)]

    def __init__(self, operate_launch_data: OperateLaunchData) -> None:
        self.ids = Id.operate_screen
        self.operate_launch_data = operate_launch_data

        super().__init__(
            id=Canvas.operate.name, classes=Tcss.operate_screen.name
        )
        self.operate_result = OperateResultData(path=operate_launch_data.path)

    def compose(self) -> ComposeResult:
        yield OperateInfo(button_id=self.operate_launch_data.button_id)
        yield RichLog(id="operate-screen-log")

    def on_mount(self) -> None:
        log_widget = self.query_one(RichLog)
        log_widget.write("placeholder for operate screen")

    def action_cancel_operation(self) -> None:
        self.dismiss(self.operate_result)

    def on_click(self, event: Click) -> None:
        if event.chain == 2:
            self.dismiss(self.operate_result)
