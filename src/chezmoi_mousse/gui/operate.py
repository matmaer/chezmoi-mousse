import dataclasses
from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from chezmoi_mousse import (
    AppType,
    BindingDescription,
    Chars,
    OperateBtn,
    PathKind,
    SectionLabels,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.shared import (
    ContentsView,
    CustomHeader,
    DiffView,
    MainSectionLabel,
    OperateButtons,
    OperateLog,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, CommandResult, OperateScreenData


__all__ = [
    "AddOperateScreen",
    "ApplyOperateScreen",
    "InitOperateScreen",
    "OperateInfo",
    "OperateScreenBase",
    "ReAddOperateScreen",
]


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
    init_clone = "[$text-primary]Initialize a new chezmoi repository from an existing one.[/]"
    init_clone_url = "[$text-primary]The URL of the remote repository to initialize from.[/]"
    init_new = "[$text-primary]Initialize a new chezmoi repository.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path[/]"
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
        elif (
            self.operate_data.splash_data is not None
            and self.operate_data.repo_url is not None
        ):
            self.repo_url = self.operate_data.repo_url

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
                OperateBtn.apply_path.dir_tooltip.rstrip(".")
                if self.path_kind == PathKind.FILE
                else OperateBtn.apply_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.apply_path)
            self.border_subtitle = Chars.apply_info_border
        elif self.operate_btn == OperateBtn.re_add_path:
            self.border_title = (
                OperateBtn.re_add_path.file_tooltip.rstrip(".")
                if self.path_kind == PathKind.FILE
                else OperateBtn.re_add_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.re_add_path)
            self.border_subtitle = Chars.re_add_info_border
        elif self.operate_btn == OperateBtn.forget_path:
            self.border_title = (
                OperateBtn.forget_path.file_tooltip.rstrip(".")
                if self.path_kind == PathKind.FILE
                else OperateBtn.forget_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.forget_path)
            self.border_subtitle = Chars.forget_info_border
        elif self.operate_btn == OperateBtn.destroy_path:
            self.border_title = (
                OperateBtn.destroy_path.file_tooltip.rstrip(".")
                if self.path_kind == PathKind.FILE
                else OperateBtn.destroy_path.dir_tooltip.rstrip(".")
            )
            lines_to_write.append(InfoLine.destroy_path)
            self.border_subtitle = Chars.destroy_info_border
        elif self.operate_btn == OperateBtn.init_new_repo:
            if OperateBtn.init_new_repo.initial_tooltip is not None:
                self.border_title = (
                    OperateBtn.init_new_repo.initial_tooltip.rstrip(".")
                )
            lines_to_write.append(InfoLine.init_new)
        elif self.operate_btn == OperateBtn.init_clone_repo:
            if OperateBtn.init_clone_repo.initial_tooltip is not None:
                self.border_title = (
                    OperateBtn.init_clone_repo.initial_tooltip.rstrip(".")
                )
            lines_to_write.append(InfoLine.init_clone)
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
        if (
            OperateBtn.apply_path == self.operate_btn
            or OperateBtn.re_add_path == self.operate_btn
        ):
            lines_to_write.append(InfoLine.diff_color)
            lines_to_write.append(
                f"[$text-primary]Operating on path: {self.path_arg}[/]"
            )
        self.update("\n".join(lines_to_write))


class OperateScreenBase(Screen["OperateScreenData"], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action="exit_operation",
            description=BindingDescription.cancel,
            show=True,
        )
    ]

    def __init__(
        self, *, ids: "AppIds", operate_data: "OperateScreenData"
    ) -> None:
        super().__init__()

        self.ids = ids
        self.operate_btn = operate_data.operate_btn
        self.operate_btn_q = self.ids.operate_button_id(
            "#", btn=self.operate_btn
        )
        self.operate_data = operate_data
        self.repo_url: str | None = None
        if self.operate_data.node_data is not None:
            self.path_arg = self.operate_data.node_data.path
            self.path_kind = self.operate_data.node_data.path_kind
        elif (
            self.operate_data.splash_data is not None
            and self.operate_data.repo_url is not None
        ):
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
        with VerticalGroup(id=self.ids.container.post_operate):
            yield MainSectionLabel(SectionLabels.operate_output)
            yield OperateLog(ids=self.ids)
        if self.operate_btn in (
            OperateBtn.init_clone_repo,
            OperateBtn.init_new_repo,
        ):
            yield OperateButtons(
                ids=self.ids, buttons=(self.operate_btn, OperateBtn.init_exit)
            )

        else:
            yield OperateButtons(
                ids=self.ids,
                buttons=(self.operate_btn, OperateBtn.operate_exit),
            )
        yield Footer(id=self.ids.footer)

    def on_mount(self) -> None:
        self.configure_buttons()
        self.configure_widgets()
        self.configure_containers()

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
            op_btn.tooltip = (
                OperateBtn.add_dir.initial_tooltip
                if self.path_kind == PathKind.DIR
                else OperateBtn.add_file.initial_tooltip
            )
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

    def configure_containers(self) -> None:
        self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        ).display = False

    def run_operate_command(self) -> "CommandResult | None":
        cmd_result: "CommandResult | None" = None
        if self.operate_btn in (OperateBtn.add_file, OperateBtn.add_dir):
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.add,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.apply_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.re_add_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.forget_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.destroy_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy,
                path_arg=self.path_arg,
                dry_run=self.app.changes_enabled,
            )
        elif self.operate_btn == OperateBtn.init_new_repo:
            self.command_result = self.app.chezmoi.perform(
                WriteCmd.init, dry_run=self.app.changes_enabled
            )
        elif self.operate_btn == OperateBtn.init_clone_repo:
            self.command_result = self.app.chezmoi.perform(
                WriteCmd.init,
                repo_url=self.repo_url,
                dry_run=self.app.changes_enabled,
            )
        else:
            self.screen.notify(
                f"Operate button not implemented: {self.operate_btn.name}",
                severity="error",
            )
        self.operate_data.command_result = cmd_result
        self.post_operate_ui_update()

    def post_operate_ui_update(self) -> None:
        pre_op_container = self.query_one(
            self.ids.container.pre_operate_q, VerticalGroup
        )
        pre_op_container.display = False
        post_op_container = self.query_one(
            self.ids.container.post_operate_q, VerticalGroup
        )
        post_op_container.display = True

        operate_button = self.query_one(self.operate_btn_q, Button)
        operate_button.disabled = True
        operate_button.tooltip = None

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

        output_log = self.query_one(self.ids.logger.operate_q, OperateLog)
        if self.operate_data.command_result is not None:
            output_log.log_cmd_results(self.operate_data.command_result)
        else:
            output_log.error("Command result is None, cannot log output.")
        self.update_bindings()

    @on(Button.Pressed, Tcss.operate_button.dot_prefix)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.label in (
            OperateBtn.operate_exit.cancel_label,
            OperateBtn.operate_exit.close_label,
        ):
            self.dismiss(self.operate_data)
        else:
            self.run_operate_command()

    def update_bindings(self) -> None:
        if self.operate_data.command_result is None:
            return
        if self.operate_btn in (
            OperateBtn.init_new_repo,
            OperateBtn.init_clone_repo,
        ):
            new_description = (
                BindingDescription.reload
                if self.operate_data.command_result.returncode == 0
                else BindingDescription.exit_app
            )
            self.update_binding_description(new_description)
        elif self.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            new_description = (
                BindingDescription.reload
                if self.operate_data.command_result.returncode == 0
                else BindingDescription.back
            )
            new_description = BindingDescription.reload
            self.update_binding_description(new_description)

    def update_binding_description(self, new_description: str) -> None:
        for key, binding in self._bindings:
            if binding.action == "exit_operation":
                updated_binding = dataclasses.replace(
                    binding, description=new_description
                )
                if key in self._bindings.key_to_bindings:
                    bindings_list = self._bindings.key_to_bindings[key]
                    for i, b in enumerate(bindings_list):
                        if b.action == "exit_operation":
                            bindings_list[i] = updated_binding
                            break
                break
            self.refresh_bindings()

    def action_exit_operation(self) -> None:
        self.dismiss(self.operate_data)


class AddOperateScreen(OperateScreenBase):
    pass


class ApplyOperateScreen(OperateScreenBase):
    pass


class ReAddOperateScreen(OperateScreenBase):
    pass


class InitOperateScreen(OperateScreenBase):
    pass
