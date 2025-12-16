from enum import StrEnum
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from chezmoi_mousse import (
    AppType,
    BindingAction,
    BindingDescription,
    Chars,
    OperateBtn,
    SectionLabels,
    Tcss,
)

from ._actionables import OperateButtons
from ._loggers import DebugLog, OperateLog
from ._screen_header import CustomHeader

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["OperateScreenBase", "OperateInfo"]


class OperateText(StrEnum):
    add_path = "[$text-primary]The path will be added to your chezmoi dotfile manager source state.[/]"
    add_subtitle = f"path on disk {Chars.right_arrow} chezmoi repo"
    apply_path = "[$text-primary]The path in the destination directory will be modified.[/]"
    apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_disabled = "[dim]Changes are currently disabled, running commands with '--dry-run' flag.[/]"
    changes_enabled = f"[$text-warning]{Chars.warning_sign} Changes currently enabled, running commands without '--dry-run' flag.{Chars.warning_sign}[/]"
    destroy_path = "[$text-error]Permanently remove the path both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    destroy_subtitle = (
        f"{Chars.x_mark} delete on disk and in chezmoi repo {Chars.x_mark}"
    )
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_path = "[$text-primary]Remove the path from the source state, i.e. stop managing them.[/]"
    forget_subtitle = f"{Chars.x_mark} leave on disk but remove from chezmoi repo {Chars.x_mark}"
    init_clone = "[$text-primary]Initialize a chezmoi from:[/]"
    init_new = "[$text-primary]Initialize a new chezmoi repository.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path.[/]"
    )
    re_add_subtitle = (
        f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    )


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, ids: "AppIds") -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateInfo")
        self.op_data = self.app.operate_data
        self.btn_enum = self.op_data.btn_enum
        self.repo_arg: bool | None = None

    def on_mount(self) -> None:
        self.set_border_titles()
        self.write_info_lines()

    def set_border_titles(self) -> None:
        self.border_title = self.op_data.btn_label
        if self.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            self.border_subtitle = OperateText.add_subtitle
        elif self.btn_enum == OperateBtn.apply_path:
            self.border_subtitle = OperateText.apply_subtitle
        elif self.btn_enum == OperateBtn.forget_path:
            self.border_subtitle = OperateText.forget_subtitle
        elif self.btn_enum == OperateBtn.destroy_path:
            self.border_subtitle = OperateText.destroy_subtitle
        elif self.btn_enum == OperateBtn.re_add_path:
            self.border_subtitle = OperateText.re_add_subtitle
        elif self.btn_enum == OperateBtn.init_repo:
            self.border_subtitle = None
        else:
            raise ValueError("No border subtitle, unknown operation")

    def write_info_lines(self) -> None:
        self.update("")
        lines_to_write: list[str] = []
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateText.changes_enabled)
        else:
            lines_to_write.append(OperateText.changes_disabled)

        if self.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            lines_to_write.append(OperateText.add_path)
        elif self.btn_enum == OperateBtn.apply_path:
            lines_to_write.append(OperateText.apply_path)
        elif self.btn_enum == OperateBtn.re_add_path:
            lines_to_write.append(OperateText.re_add_path)
        elif self.btn_enum == OperateBtn.forget_path:
            lines_to_write.append(OperateText.forget_path)
        elif self.btn_enum == OperateBtn.destroy_path:
            lines_to_write.append(OperateText.destroy_path)
        elif self.btn_enum == OperateBtn.init_repo:
            if self.op_data.btn_label == OperateBtn.init_repo.init_clone_label:
                lines_to_write.append(
                    f"{OperateText.init_clone} [$text-warning]{self.repo_arg}[/]"
                )
            else:
                lines_to_write.append(OperateText.init_new)

        if self.btn_enum not in (OperateBtn.apply_path, OperateBtn.init_repo):
            if self.git_autocommit is True:
                lines_to_write.append(OperateText.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(OperateText.autopush)
        # show git diff color info
        if self.btn_enum in (OperateBtn.apply_path, OperateBtn.re_add_path):
            lines_to_write.append(OperateText.diff_color)
        if self.op_data.node_data is not None:
            lines_to_write.append(
                f"[$text-primary]Operating on path: {self.op_data.node_data.path}[/]"
            )
        self.update("\n".join(lines_to_write))


class OperateScreenBase(Screen[None], AppType):
    def __init__(self, *, ids: "AppIds") -> None:
        super().__init__()
        self.ids = ids
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.op_data = self.app.operate_data

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

    def update_buttons(self) -> None:
        if (
            self.app.operate_cmd_result is None
            or self.app.operate_cmd_result.dry_run is True
        ):
            return
        self.op_btn.disabled = True
        self.op_btn.tooltip = None
        self.exit_btn.label = OperateBtn.operate_exit.reload_label

    def update_key_binding(self) -> None:
        if (
            self.app.operate_cmd_result is not None
            and self.app.operate_cmd_result.dry_run is True
        ):
            return
        new_description = BindingDescription.reload
        self.app.update_binding_description(
            BindingAction.exit_screen, new_description
        )

    def write_to_output_log(self) -> None:
        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        if self.app.operate_cmd_result is not None:
            output_log.log_cmd_results(self.app.operate_cmd_result)
