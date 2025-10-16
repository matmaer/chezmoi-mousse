from enum import StrEnum

from textual.widgets import Static

from chezmoi_mousse import AppType, Chars, OperateBtn, Tcss

__all__ = ["OperateInfo"]


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
        diff_color = "[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
        forget_file = "[$text-primary]Remove the file from the source state, i.e. stop managing them.[/]"
        # forget_dir = "[$text-primary]Remove the directory from the source state, i.e. stop managing them.[/]"
        re_add_file = "[$text-primary]Overwrite the source state with current local file[/]"
        # re_add_dir = "[$text-primary]Overwrite the source state with thecurrent local directory[/]"

    def __init__(self, *, operate_btn: OperateBtn) -> None:
        self.operate_btn = operate_btn
        super().__init__(
            id=OperateInfo.Strings.container_id, classes=Tcss.operate_info.name
        )

    def on_mount(self) -> None:
        lines_to_write: list[str] = []

        # show command help and set the subtitle
        if OperateBtn.apply_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.apply_file.value)
            self.border_subtitle = Chars.apply_file_info_border
        elif OperateBtn.re_add_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.re_add_file.value)
            self.border_subtitle = Chars.re_add_file_info_border
        elif OperateBtn.add_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.add_file.value)
            self.border_subtitle = Chars.add_file_info_border
        elif OperateBtn.forget_file == self.operate_btn:
            lines_to_write.append(OperateInfo.Strings.forget_file.value)
            self.border_subtitle = Chars.forget_file_info_border
        elif OperateBtn.destroy_file == self.operate_btn:
            lines_to_write.extend(OperateInfo.Strings.destroy_file.value)
            self.border_subtitle = Chars.destroy_file_info_border
        # show git auto warnings
        if not OperateBtn.apply_file == self.operate_btn:
            assert (
                self.git_autocommit is not None
                and self.git_autopush is not None
            )
            if self.git_autocommit is True:
                lines_to_write.append(OperateInfo.Strings.auto_commit.value)
            if self.git_autopush is True:
                lines_to_write.append(OperateInfo.Strings.autopush.value)
        # show git diff color info
        if (
            OperateBtn.apply_file == self.operate_btn
            or OperateBtn.re_add_file == self.operate_btn
        ):
            lines_to_write.extend(OperateInfo.Strings.diff_color.value)
        self.update("\n".join(lines_to_write))
