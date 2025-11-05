from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Static

from chezmoi_mousse import (
    AppType,
    CanvasName,
    Chars,
    OperateBtn,
    OperateScreenData,
    Tcss,
    ViewName,
    WriteCmd,
)

from ..shared.button_groups import OperateBtnHorizontal
from ..shared.canvas_ids import CanvasIds
from ..shared.contents_view import ContentsView
from ..shared.diff_view import DiffView
from ..shared.loggers import OutputLog
from ..shared.section_headers import SectionLabel

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

__all__ = ["OperateInfo", "OperateScreen"]


class ContainerIds(StrEnum):
    operate_btn = "operate_btn_container_id"
    pre_operate = "pre_operate_container_id"
    post_operate = "post_operate_container_id"


class InfoStrings(StrEnum):
    add_path = "[$text-primary]The path will be added to your chezmoi dotfile manager source state.[/]"
    apply_path = "[$text-primary]The path in the destination directory will be modified.[/]"
    auto_commit = f"[$text-warning]{Chars.warning_sign} Auto commit is enabled: files will also be committed.{Chars.warning_sign}[/]"
    autopush = f"[$text-warning]{Chars.warning_sign} Auto push is enabled: files will be pushed to the remote.{Chars.warning_sign}[/]"
    changes_disabled = (
        "[$text-success]Changes are currently disabled (dry-run mode)"
    )
    changes_enabled = f"[$text-warning]{Chars.warning_sign} Changes currently enabled, running without '--dry-run' flag.{Chars.warning_sign}[/]"
    destroy_path = "[$text-error]Permanently remove the path both from your home directory and chezmoi's source directory, make sure you have a backup![/]"
    diff_color = f"[$text-success]+ green lines will be added[/]\n[$text-error]- red lines will be removed[/]\n[dim]{Chars.bullet} dimmed lines for context[/]"
    forget_path = "[$text-primary]Remove the path from the source state, i.e. stop managing them.[/]"
    re_add_path = (
        "[$text-primary]Overwrite the source state with current local path[/]"
    )


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, operate_screen_data: OperateScreenData) -> None:
        self.operate_btn = operate_screen_data.operate_btn
        self.node_data = operate_screen_data.node_data
        super().__init__(classes=Tcss.operate_info.name)

    def on_mount(self) -> None:
        lines_to_write: list[str] = []
        if self.app.changes_enabled is True:
            lines_to_write.append(InfoStrings.changes_enabled)
        else:
            lines_to_write.append(InfoStrings.changes_disabled)
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
            action="exit_operation",
            description="Press the escape key to exit",
            show=True,
        )
    ]

    def __init__(self, operate_data: "OperateScreenData") -> None:
        self.ids = CanvasIds(CanvasName.operate_screen)
        super().__init__(
            id=self.ids.canvas_name, classes=Tcss.operate_screen.name
        )
        self.operate_data = operate_data
        self.exit_btn_id = self.ids.button_id(btn=OperateBtn.exit_button)
        self.exit_btn_qid = self.ids.button_id("#", btn=OperateBtn.exit_button)
        self.operate_btn_qid = self.ids.button_id(
            "#", btn=self.operate_data.operate_btn
        )
        self.wriet_output_log_view_qid = self.ids.view_id(
            "#", view=ViewName.write_output_log_view
        )

    def compose(self) -> ComposeResult:
        yield SectionLabel("Operate Context")
        yield OperateInfo(self.operate_data)
        with Vertical(id=ContainerIds.pre_operate.value):
            if self.operate_data.operate_btn == OperateBtn.apply_path:
                yield DiffView(ids=self.ids, reverse=False)
            elif self.operate_data.operate_btn == OperateBtn.re_add_path:
                yield DiffView(ids=self.ids, reverse=True)
            elif self.operate_data.operate_btn in (
                OperateBtn.add_file,
                OperateBtn.add_dir,
            ):
                yield ContentsView(ids=self.ids)
            elif self.operate_data.operate_btn in (
                OperateBtn.forget_path,
                OperateBtn.destroy_path,
            ):
                yield DiffView(ids=self.ids, reverse=False)
        with Vertical(id=ContainerIds.post_operate.value):
            yield SectionLabel("Operate Command Output")
            yield OutputLog(
                ids=self.ids, view_name=ViewName.write_output_log_view
            )
        with Vertical(id=ContainerIds.operate_btn.value):
            yield OperateBtnHorizontal(
                ids=self.ids,
                buttons=(
                    self.operate_data.operate_btn,
                    OperateBtn.exit_button,
                ),
            )
        yield Footer()

    def on_mount(self) -> None:
        self.configure_buttons()
        self.configure_widgets()
        self.configure_containers()

    def configure_widgets(self) -> None:
        if self.operate_data.operate_btn in (
            OperateBtn.apply_path,
            OperateBtn.re_add_path,
        ):
            diff_view = self.query_exactly_one(DiffView)
            diff_view.path = self.operate_data.node_data.path

        elif self.operate_data.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
        ):
            contents_view = self.query_exactly_one(ContentsView)
            contents_view.path = self.operate_data.node_data.path
        elif self.operate_data.operate_btn in (
            OperateBtn.forget_path,
            OperateBtn.destroy_path,
        ):
            diff_view = self.query_exactly_one(DiffView)
            diff_view.path = self.operate_data.node_data.path

        screen_output_log = self.query_one(
            self.wriet_output_log_view_qid, OutputLog
        )
        screen_output_log.auto_scroll = False

    def configure_buttons(self) -> None:
        operate_button = self.query_one(self.operate_btn_qid, Button)
        operate_button.disabled = False
        operate_button.tooltip = None
        exit_button = self.query_one(self.exit_btn_qid, Button)
        exit_button.disabled = False
        exit_button.tooltip = None

        if self.operate_data.operate_btn == OperateBtn.apply_path:
            operate_button.label = (
                OperateBtn.apply_path.dir_label
                if self.operate_data.node_data.path_type == "dir"
                else OperateBtn.apply_path.file_label
            )

        elif self.operate_data.operate_btn == OperateBtn.re_add_path:
            operate_button.label = (
                OperateBtn.re_add_path.dir_label
                if self.operate_data.node_data.path_type == "dir"
                else OperateBtn.re_add_path.file_label
            )
        elif self.operate_data.operate_btn == OperateBtn.add_dir:
            operate_button.label = (
                OperateBtn.add_dir.initial_label
                if self.operate_data.node_data.path_type == "dir"
                else OperateBtn.add_file.initial_label
            )

    def configure_containers(self) -> None:
        post_operate_container = self.query_one(
            f"#{ContainerIds.post_operate.value}", Vertical
        )
        post_operate_container.display = False

    def run_operate_command(self) -> "CommandResult | None":
        cmd_result: "CommandResult | None" = None
        if self.operate_data.operate_btn in (
            OperateBtn.add_file,
            OperateBtn.add_dir,
        ):
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.add, path_arg=self.operate_data.node_data.path
            )
        elif self.operate_data.operate_btn == OperateBtn.apply_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.apply, path_arg=self.operate_data.node_data.path
            )
        elif self.operate_data.operate_btn == OperateBtn.re_add_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.re_add, path_arg=self.operate_data.node_data.path
            )
        elif self.operate_data.operate_btn == OperateBtn.forget_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.forget, path_arg=self.operate_data.node_data.path
            )
        elif self.operate_data.operate_btn == OperateBtn.destroy_path:
            cmd_result = self.app.chezmoi.perform(
                WriteCmd.destroy, path_arg=self.operate_data.node_data.path
            )
        else:
            self.screen.notify(
                f"Operate button not implemented: {self.operate_data.operate_btn.name}",
                severity="error",
            )
        self.operate_data.operation_executed = True
        self.operate_data.command_result = cmd_result
        self.post_operate_ui_update()

    def post_operate_ui_update(self) -> None:
        pre_operate_container = self.query_one(
            f"#{ContainerIds.pre_operate.value}", Vertical
        )
        pre_operate_container.display = False
        post_operate_container = self.query_one(
            f"#{ContainerIds.post_operate.value}", Vertical
        )
        post_operate_container.display = True

        operate_button = self.query_one(self.operate_btn_qid, Button)
        operate_button.disabled = True
        operate_button.tooltip = None

        operate_exit_button = self.query_one(self.exit_btn_qid, Button)
        operate_exit_button.label = OperateBtn.exit_button.close_button_label

        if self.operate_data.command_result is not None:
            screen_output_log = self.query_one(
                self.wriet_output_log_view_qid, OutputLog
            )
            screen_output_log.log_cmd_results(self.operate_data.command_result)

    @on(Button.Pressed, Tcss.operate_button.value)
    def handle_operate_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == self.exit_btn_id:
            self.dismiss(self.operate_data)
        else:
            self.run_operate_command()

    def action_exit_operation(self) -> None:
        self.dismiss(self.operate_data)
