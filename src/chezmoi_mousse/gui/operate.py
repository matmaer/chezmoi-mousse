from enum import StrEnum

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from chezmoi_mousse import (
    IDS,
    AppType,
    BindingAction,
    BindingDescription,
    Chars,
    OperateBtn,
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
    InitCompletedMsg,
    MainSectionLabel,
    OperateButtons,
    OperateLog,
    PrettyTemplateData,
)

__all__ = ["OperateInfo", "OperateScreen"]


class InfoBorderTitle(StrEnum):
    init_clone = "Run 'chezmoi init' from an existing repository"
    init_new = "Run 'chezmoi init' with default settings"


class InfoBorderSubtitle(StrEnum):
    add = f"local {Chars.right_arrow} chezmoi"
    apply = f"local {Chars.left_arrow} chezmoi"
    destroy = f"{Chars.x_mark} destroy {Chars.x_mark}"
    forget = f"{Chars.x_mark} forget {Chars.x_mark}"


class InfoLine(StrEnum):
    add_path = "[$text-primary]The path will be added to your chezmoi dotfile manager source state.[/]"
    apply_path = "[$text-primary]The path in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_disabled = "[dim]Changes are currently disabled, running commands with '--dry-run' flag.[/]"
    changes_enabled = f"[$text-warning]{Chars.warning_sign} Changes currently enabled, running commands without '--dry-run' flag.{Chars.warning_sign}[/]"
    destroy_path = "[$text-error]Permanently remove the path both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_path = "[$text-primary]Remove the path from the source state, i.e. stop managing them.[/]"
    init_clone = "[$text-primary]Initialize a chezmoi from:[/]"
    init_new = "[$text-primary]Initialize a new chezmoi repository.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path.[/]"
    )


class InitCollapsibles(VerticalGroup):
    def __init__(self, splash_data: "SplashData") -> None:
        super().__init__()
        self.splash_data = splash_data

    def on_mount(self) -> None:
        self.mount(
            CustomCollapsible(
                DoctorTable(
                    ids=IDS.operate, doctor_data=self.splash_data.doctor
                ),
                title="Doctor Output",
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

    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateInfo")
        self.op_data = self.app.operate_data

    def on_mount(self) -> None:
        self.op_btn = self.op_data.btn_enum
        self.set_border_titles()
        self.write_info_lines()

    def set_border_titles(self) -> None:
        self.border_title = self.op_data.btn_label
        if self.op_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.re_add_path,
        ):
            self.border_subtitle = InfoBorderSubtitle.add
        elif self.op_btn == OperateBtn.apply_path:
            self.border_subtitle = InfoBorderSubtitle.apply
        elif self.op_btn == OperateBtn.forget_path:
            self.border_subtitle = InfoBorderSubtitle.forget
        elif self.op_btn == OperateBtn.destroy_path:
            self.border_subtitle = InfoBorderSubtitle.destroy

    def write_info_lines(self) -> None:
        self.update("")
        lines_to_write: list[str] = []
        if self.op_btn in (OperateBtn.add_file, OperateBtn.add_dir):
            lines_to_write.append(InfoLine.add_path)
        elif self.op_btn == OperateBtn.apply_path:
            lines_to_write.append(InfoLine.apply_path)
        elif self.op_btn == OperateBtn.re_add_path:
            lines_to_write.append(InfoLine.re_add_path)
        elif self.op_btn == OperateBtn.forget_path:
            lines_to_write.append(InfoLine.forget_path)
        elif self.op_btn == OperateBtn.destroy_path:
            lines_to_write.append(InfoLine.destroy_path)
        elif self.op_btn == OperateBtn.init_new_repo:
            lines_to_write.append(InfoLine.init_new)
        elif self.op_btn == OperateBtn.init_clone_repo:
            lines_to_write.append(
                f"{InfoLine.init_clone} [$text-warning]{self.op_data.repo_url}[/]"
            )
        if self.app.changes_enabled is True:
            lines_to_write.append(InfoLine.changes_enabled)
        else:
            lines_to_write.append(InfoLine.changes_disabled)
        if self.op_btn not in (
            OperateBtn.apply_path,
            OperateBtn.init_new_repo,
            OperateBtn.init_clone_repo,
        ):
            if self.git_autocommit is True:
                lines_to_write.append(InfoLine.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(InfoLine.autopush)
        # show git diff color info
        if self.op_btn in (OperateBtn.apply_path, OperateBtn.re_add_path):
            lines_to_write.append(InfoLine.diff_color)
        if self.op_data.node_data is not None:
            lines_to_write.append(
                f"[$text-primary]Operating on path: {self.op_data.node_data.path}[/]"
            )
        self.update("\n".join(lines_to_write))


class OperateScreen(Screen[None], AppType):

    def __init__(self) -> None:
        super().__init__()
        if self.app.operate_data is None:
            raise ValueError("self.app.operate_data is None in OperateScreen")
        self.op_data = self.app.operate_data

    def compose(self) -> ComposeResult:
        yield CustomHeader(IDS.operate)
        with VerticalGroup(id=IDS.operate.container.pre_operate):
            yield OperateInfo()
        with VerticalGroup(id=IDS.operate.container.post_operate):
            yield MainSectionLabel(SectionLabels.operate_output)
            yield OperateLog(ids=IDS.operate)
        yield OperateButtons(
            ids=IDS.operate,
            buttons=(self.op_data.btn_enum, OperateBtn.operate_exit),
        )
        yield Footer(id=IDS.operate.footer)

    def on_mount(self) -> None:
        self.query_one(
            IDS.operate.container.post_operate_q, VerticalGroup
        ).display = False
        self.op_btn = self.query_one(
            IDS.operate.operate_button_id("#", btn=self.op_data.btn_enum),
            Button,
        )
        self.exit_btn = self.query_one(
            IDS.operate.operate_button_id("#", btn=OperateBtn.operate_exit),
            Button,
        )
        if self.op_data.node_data is not None:
            self.path_arg = self.op_data.node_data.path
        elif self.op_data.repo_url is not None:
            self.repo_url = self.op_data.repo_url
        self.mount_pre_operate_widgets()
        self.configure_buttons()

    def mount_pre_operate_widgets(self) -> None:
        pre_op_container = self.query_one(
            IDS.operate.container.pre_operate_q, VerticalGroup
        )
        if self.op_data.btn_enum == OperateBtn.apply_path:
            pre_op_container.mount(DiffView(ids=IDS.operate, reverse=False))
        elif self.op_data.btn_enum == OperateBtn.re_add_path:
            pre_op_container.mount(DiffView(ids=IDS.operate, reverse=True))
        elif self.op_data.btn_enum in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            pre_op_container.mount(ContentsView(ids=IDS.operate))
        elif (
            self.op_data.btn_enum
            in (OperateBtn.init_new_repo, OperateBtn.init_clone_repo)
            and self.app.splash_data is not None
        ):
            pre_op_container.mount(
                MainSectionLabel(SectionLabels.operate_context)
            )
            pre_op_container.mount(
                InitCollapsibles(splash_data=self.app.splash_data)
            )
        if self.op_data.btn_enum in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            diff_view = self.query_one(IDS.operate.container.diff_q, DiffView)
            diff_view.path = self.path_arg
        elif self.op_data.btn_enum in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            contents_view = self.query_one(
                IDS.operate.container.contents_q, ContentsView
            )
            contents_view.path = self.path_arg

    def configure_buttons(self) -> None:
        self.op_btn.label = self.op_data.btn_label
        self.op_btn.tooltip = self.op_data.btn_tooltip
        if self.op_data.btn_enum in (
            OperateBtn.init_new_repo,
            OperateBtn.init_clone_repo,
        ):
            self.exit_btn.label = OperateBtn.operate_exit.exit_app_label

    def run_operate_command(self) -> None:
        if self.op_data.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.apply_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.re_add_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.forget_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.destroy_path:
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=self.path_arg,
                changes_enabled=self.app.changes_enabled,
            )
        elif self.op_data.btn_enum == OperateBtn.init_new_repo:
            self.app.init_cmd_issued = True
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.init, changes_enabled=self.app.changes_enabled
            )
        elif self.op_data.btn_enum == OperateBtn.init_clone_repo:
            self.app.init_cmd_issued = True
            self.app.operate_cmd_result = self.app.chezmoi.perform(
                WriteCmd.init,
                repo_url=self.repo_url,
                changes_enabled=self.app.changes_enabled,
            )

        self.update_visibility()
        self.write_to_output_log()
        self.update_buttons()
        self.update_key_binding()

    def write_to_output_log(self) -> None:
        output_log = self.query_one(IDS.operate.logger.operate_q, OperateLog)
        if self.app.operate_cmd_result is not None:
            output_log.log_cmd_results(self.app.operate_cmd_result)
        else:
            self.notify("No command result to log.", severity="error")

    def update_key_binding(self) -> None:
        new_description = (
            BindingDescription.reload
            if self.op_data.btn_enum
            in (OperateBtn.init_new_repo, OperateBtn.init_clone_repo)
            else BindingDescription.close
        )
        self.app.update_binding_description(
            BindingAction.exit_screen, new_description
        )

    def update_visibility(self) -> None:
        pre_op_container = self.query_one(
            IDS.operate.container.pre_operate_q, VerticalGroup
        )
        pre_op_container.display = False
        post_op_container = self.query_one(
            IDS.operate.container.post_operate_q, VerticalGroup
        )
        post_op_container.display = True

    def update_buttons(self) -> None:
        self.op_btn.disabled = True
        self.op_btn.tooltip = None
        operate_exit_button = self.query_one(
            IDS.operate.operate_button_id("#", btn=OperateBtn.operate_exit),
            Button,
        )
        if self.op_data.btn_enum in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            operate_exit_button.label = OperateBtn.operate_exit.close_label
        elif self.op_data.btn_enum in (
            OperateBtn.init_new_repo,
            OperateBtn.init_clone_repo,
        ):
            operate_exit_button.label = OperateBtn.operate_exit.reload_label

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label == OperateBtn.operate_exit.exit_app_label:
            self.app.exit()
        elif event.button.label in (OperateBtn.operate_exit.reload_label,):
            self.app.post_message(InitCompletedMsg())
        elif event.button.label == OperateBtn.operate_exit.cancel_label:
            self.app.operate_cmd_result = None
            self.dismiss()
        elif event.button.label in (
            OperateBtn.operate_exit.close_label,
            OperateBtn.operate_exit.reload_label,
        ):
            self.dismiss()
        else:
            self.run_operate_command()
