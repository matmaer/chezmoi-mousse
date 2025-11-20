"""Contains subclassed textual classes shared between the AddTab, ApplyTab and
ReAddTab."""

from enum import StrEnum
from typing import TYPE_CHECKING

from textual.widgets import Static

from chezmoi_mousse import AppType, Chars, OperateBtn, OperateScreenData

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["OperateInfo"]


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

    def __init__(
        self, *, ids: "AppIds", operate_screen_data: OperateScreenData
    ) -> None:
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
