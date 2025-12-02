from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from chezmoi_mousse import (
    AppType,
    BindingAction,
    BindingDescription,
    Chars,
    OperateBtn,
    PathKind,
    SectionLabels,
    SplashData,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    ContentsView,
    CustomCollapsible,
    CustomHeader,
    DiffView,
    DoctorTable,
    MainSectionLabel,
    OperateButtons,
    OperateLog,
    PrettyTemplateData,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, CommandResult, OperateScreenData


__all__ = ["OperateInfo", "OperateScreen"]


class InfoBorderTitle(StrEnum):
    add_dir = OperateBtn.add_dir.enabled_tooltip.rstrip(".")
    add_file = OperateBtn.add_file.enabled_tooltip.rstrip(".")
    apply_dir = OperateBtn.apply_path.dir_tooltip.rstrip(".")
    apply_file = OperateBtn.apply_path.file_tooltip.rstrip(".")
    destroy_dir = "Run 'chezmoi destroy' on the directory"
    destroy_file = "Run 'chezmoi destroy' on the file"
    forget_dir = OperateBtn.forget_path.dir_tooltip.rstrip(".")
    forget_file = OperateBtn.forget_path.file_tooltip.rstrip(".")
    init_clone = "Run 'chezmoi init' from an existing repository"
    init_new = "Run 'chezmoi init' with default settings"
    re_add_dir = OperateBtn.re_add_path.dir_tooltip.rstrip(".")
    re_add_file = OperateBtn.re_add_path.file_tooltip.rstrip(".")


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
    init_clone = "[$text-primary]Initialize a chezmoi from:[/]"
    init_new = "[$text-primary]Initialize a new chezmoi repository.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path[/]"
    )


class InitCollapsibles(VerticalGroup):
    def __init__(self, ids: "AppIds", splash_data: "SplashData") -> None:
        super().__init__()
        self.ids = ids
        self.splash_data = splash_data

    def on_mount(self) -> None:
        self.mount(
            CustomCollapsible(
                DoctorTable(ids=self.ids, doctor_data=self.splash_data.doctor),
                title="Doctor Output",
            )
        )
        self.mount(
            CustomCollapsible(
                Static(self.splash_data.cat_config.std_out, markup=False),
                title="Cat Config Output",
            )
        )
        self.mount(
            CustomCollapsible(
                PrettyTemplateData(self.splash_data.template_data),
                title="Template Data Output",
            )
        )


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, *, operate_data: "OperateScreenData") -> None:
        super().__init__()
        self.operate_btn = operate_data.operate_btn
        self.operate_data = operate_data
        if self.operate_data.node_data is not None:
            self.path_arg = self.operate_data.node_data.path
            self.path_kind = self.operate_data.node_data.path_kind
        elif self.operate_data.repo_url is not None:
            self.repo_url = self.operate_data.repo_url

    def on_mount(self) -> None:
        self.write_info_lines()

    def write_info_lines(self) -> None:
        self.update("")
        lines_to_write: list[str] = []
        if self.operate_btn == OperateBtn.add_file:
            self.border_title = InfoBorderTitle.add_file
            lines_to_write.append(InfoLine.add_path)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.add_dir:
            self.border_title = InfoBorderTitle.add_dir
            lines_to_write.append(InfoLine.add_path)
            self.border_subtitle = Chars.add_info_border
        elif self.operate_btn == OperateBtn.apply_path:
            self.border_title = (
                InfoBorderTitle.apply_file
                if self.path_kind == PathKind.FILE
                else InfoBorderTitle.apply_dir
            )
            lines_to_write.append(InfoLine.apply_path)
            self.border_subtitle = Chars.apply_info_border
        elif self.operate_btn == OperateBtn.re_add_path:
            self.border_title = (
                InfoBorderTitle.re_add_file
                if self.path_kind == PathKind.FILE
                else InfoBorderTitle.re_add_dir
            )
            lines_to_write.append(InfoLine.re_add_path)
            self.border_subtitle = Chars.re_add_info_border
        elif self.operate_btn == OperateBtn.forget_path:
            self.border_title = (
                InfoBorderTitle.forget_file
                if self.path_kind == PathKind.FILE
                else InfoBorderTitle.forget_dir
            )
            lines_to_write.append(InfoLine.forget_path)
            self.border_subtitle = Chars.forget_info_border
        elif self.operate_btn == OperateBtn.destroy_path:
            self.border_title = (
                InfoBorderTitle.destroy_file
                if self.path_kind == PathKind.FILE
                else InfoBorderTitle.destroy_dir
            )
            lines_to_write.append(InfoLine.destroy_path)
            self.border_subtitle = Chars.destroy_info_border
        elif self.operate_btn == OperateBtn.init_new_repo:
            self.border_title = InfoBorderTitle.init_new
            lines_to_write.append(InfoLine.init_new)
        elif self.operate_btn == OperateBtn.init_clone_repo:
            self.border_title = InfoBorderTitle.init_clone
            lines_to_write.append(
                f"{InfoLine.init_clone} [$text-warning]{self.repo_url}[/]"
            )

        if self.app.changes_enabled is True:
            lines_to_write.append(InfoLine.changes_enabled)
        else:
            lines_to_write.append(InfoLine.changes_disabled)
        if self.operate_btn not in (
            OperateBtn.apply_path,
            OperateBtn.init_new_repo,
            OperateBtn.init_clone_repo,
        ):
            if self.git_autocommit is True:
                lines_to_write.append(InfoLine.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(InfoLine.autopush)
        # show git diff color info
        if self.operate_btn in (OperateBtn.apply_path, OperateBtn.re_add_path):
            lines_to_write.append(InfoLine.diff_color)
            lines_to_write.append(
                f"[$text-primary]Operating on path: {self.path_arg}[/]"
            )
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen["OperateScreenData | None"], AppType):

    def __init__(
        self,
        *,
        ids: "AppIds",
        operate_data: "OperateScreenData",
        splash_data: "SplashData | None" = None,
    ) -> None:
        super().__init__()

        self.ids = ids
        self.operate_btn = operate_data.operate_btn
        self.operate_btn_q = self.ids.operate_button_id(
            "#", btn=self.operate_btn
        )
        self.operate_data = operate_data
        self.splash_data = splash_data
        self.repo_url: str | None = None
        if self.operate_data.node_data is not None:
            self.path_arg = self.operate_data.node_data.path
            self.path_kind = self.operate_data.node_data.path_kind
        elif self.operate_data.repo_url is not None:
            self.repo_url = self.operate_data.repo_url

    def compose(self) -> ComposeResult:
        yield CustomHeader(self.ids)
        with VerticalGroup(id=self.ids.container.pre_operate):
            yield OperateInfo(operate_data=self.operate_data)
            yield MainSectionLabel(SectionLabels.operate_context)
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
            elif (
                self.operate_btn
                in (OperateBtn.init_new_repo, OperateBtn.init_clone_repo)
                and self.splash_data is not None
            ):
                yield InitCollapsibles(
                    ids=self.ids, splash_data=self.splash_data
                )
        with VerticalGroup(id=self.ids.container.post_operate):
            yield MainSectionLabel(SectionLabels.operate_output)
            yield OperateLog(ids=self.ids)
        yield OperateButtons(
            ids=self.ids, buttons=(self.operate_btn, OperateBtn.operate_exit)
        )
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        ).display = False
        self.configure_buttons()
        self.configure_widgets()

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
        op_btn = self.query_one(self.operate_btn_q, Button)

        if self.operate_btn == OperateBtn.apply_path:
            op_btn.label = OperateBtn.apply_path.label(self.path_kind)
            op_btn.tooltip = OperateBtn.apply_path.tooltip(self.path_kind)
        elif self.operate_btn == OperateBtn.re_add_path:
            op_btn.label = OperateBtn.re_add_path.label(self.path_kind)
            op_btn.tooltip = OperateBtn.re_add_path.tooltip(self.path_kind)
        elif self.operate_btn == OperateBtn.add_dir:
            op_btn.label = OperateBtn.add_dir.label(self.path_kind)
            op_btn.tooltip = OperateBtn.add_dir.initial_tooltip
        elif self.operate_btn == OperateBtn.add_file:
            op_btn.label = OperateBtn.add_file.label(self.path_kind)
            op_btn.tooltip = OperateBtn.add_file.initial_tooltip
        elif self.operate_btn == OperateBtn.forget_path:
            op_btn.label = OperateBtn.forget_path.label(self.path_kind)
            op_btn.tooltip = (
                OperateBtn.forget_path.dir_tooltip
                if self.path_kind == PathKind.DIR
                else OperateBtn.forget_path.file_tooltip
            )
        elif self.operate_btn == OperateBtn.destroy_path:
            op_btn.label = OperateBtn.destroy_path.label(self.path_kind)
            op_btn.tooltip = (
                OperateBtn.destroy_path.dir_tooltip
                if self.path_kind == PathKind.DIR
                else OperateBtn.destroy_path.file_tooltip
            )
        elif self.operate_btn == OperateBtn.init_new_repo:
            op_btn.label = OperateBtn.init_new_repo.initial_label
            op_btn.tooltip = OperateBtn.init_new_repo.initial_tooltip
        elif self.operate_btn == OperateBtn.init_clone_repo:
            op_btn.label = OperateBtn.init_clone_repo.initial_label
            op_btn.tooltip = OperateBtn.init_clone_repo.initial_tooltip

    def run_operate_command(self) -> "CommandResult | None":
        if self.operate_btn in (OperateBtn.add_file, OperateBtn.add_dir):
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.apply_path:
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.re_add_path:
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.forget_path:
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.destroy_path:
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.init_new_repo:
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.init, changes_enabled=self.app.changes_enabled
            )
        elif self.operate_btn == OperateBtn.init_clone_repo:
            self.operate_data.command_result = self.app.chezmoi.perform(
                WriteCmd.init,
                repo_url=self.repo_url,
                changes_enabled=self.app.changes_enabled,
            )
        else:
            self.screen.notify(
                f"Operate button not implemented: {self.operate_btn.name}",
                severity="error",
            )

        self.update_visibility()
        self.write_to_output_log()
        self.update_operate_button()
        self.update_exit_button()
        self.update_key_binding()

    def write_to_output_log(self) -> None:
        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        if self.operate_data.command_result is not None:
            output_log.log_cmd_results(self.operate_data.command_result)
        else:
            output_log.error("Command result is None, cannot log output.")

    def update_key_binding(self) -> None:
        new_description = (
            BindingDescription.reload
            if self.operate_btn
            in (OperateBtn.init_new_repo, OperateBtn.init_clone_repo)
            else BindingDescription.close
        )
        self.app.update_binding_description(
            BindingAction.exit_screen, new_description
        )

    def update_visibility(self) -> None:
        pre_op_container = self.query_one(
            self.ids.container.pre_operate_q, VerticalGroup
        )
        pre_op_container.display = False
        post_op_container = self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        )
        post_op_container.display = True

    def update_operate_button(self) -> None:
        operate_button = self.query_one(self.operate_btn_q, Button)
        operate_button.disabled = True
        operate_button.tooltip = None

    def update_exit_button(self) -> None:
        operate_exit_button = self.query_one(
            self.ids.operate_btn.operate_exit_q, Button
        )
        if self.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            operate_exit_button.label = OperateBtn.operate_exit.close_label
        elif self.operate_btn in (
            OperateBtn.init_new_repo,
            OperateBtn.init_clone_repo,
        ):
            operate_exit_button.label = OperateBtn.operate_exit.reload_label

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label in (
            OperateBtn.operate_exit.cancel_label,
            OperateBtn.operate_exit.close_label,
        ):
            self.app.operate_data = self.operate_data
            self.dismiss(self.operate_data)
        else:
            self.run_operate_command()
