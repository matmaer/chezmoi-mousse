from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalGroup
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from chezmoi_mousse import (
    AppType,
    BindingAction,
    BindingDescription,
    OperateBtn,
    OperateStrings,
    SectionLabels,
    Tcss,
)

from ._actionables import OperateButtons
from ._loggers import DebugLog, OperateLog
from ._screen_header import CustomHeader

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["OperateScreenBase", "OperateInfo"]


class OperateInfo(Static, AppType):

    git_autocommit: bool | None = None
    git_autopush: bool | None = None

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.static.operate_info)
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
            self.border_subtitle = OperateStrings.add_subtitle
        elif self.btn_enum == OperateBtn.apply_path:
            self.border_subtitle = OperateStrings.apply_subtitle
        elif self.btn_enum == OperateBtn.forget_path:
            self.border_subtitle = OperateStrings.forget_subtitle
        elif self.btn_enum == OperateBtn.destroy_path:
            self.border_subtitle = OperateStrings.destroy_subtitle
        elif self.btn_enum == OperateBtn.re_add_path:
            self.border_subtitle = OperateStrings.re_add_subtitle
        elif self.btn_enum == OperateBtn.init_repo:
            self.border_subtitle = None
        else:
            raise ValueError("No border subtitle, unknown operation")

    def write_info_lines(self) -> None:
        self.update("")
        lines_to_write: list[str] = []
        if self.app.changes_enabled is True:
            lines_to_write.append(OperateStrings.changes_enabled)
        else:
            lines_to_write.append(OperateStrings.changes_disabled)

        if self.btn_enum in (OperateBtn.add_file, OperateBtn.add_dir):
            lines_to_write.append(OperateStrings.add_path)
        elif self.btn_enum == OperateBtn.apply_path:
            lines_to_write.append(OperateStrings.apply_path)
        elif self.btn_enum == OperateBtn.re_add_path:
            lines_to_write.append(OperateStrings.re_add_path)
        elif self.btn_enum == OperateBtn.forget_path:
            lines_to_write.append(OperateStrings.forget_path)
        elif self.btn_enum == OperateBtn.destroy_path:
            lines_to_write.append(OperateStrings.destroy_path)
        elif self.btn_enum == OperateBtn.init_repo:
            if self.op_data.btn_label == OperateBtn.init_repo.init_clone_label:
                lines_to_write.append(
                    f"{OperateStrings.init_clone} [$text-warning]{self.repo_arg}[/]"
                )
            else:
                lines_to_write.append(OperateStrings.init_new)

        if self.btn_enum not in (OperateBtn.apply_path, OperateBtn.init_repo):
            if self.git_autocommit is True:
                lines_to_write.append(OperateStrings.auto_commit)
            if self.git_autopush is True:
                lines_to_write.append(OperateStrings.auto_push)
        # show git diff color info
        if self.btn_enum in (OperateBtn.apply_path, OperateBtn.re_add_path):
            lines_to_write.append(OperateStrings.diff_color)
        if self.op_data.node_data is not None:
            lines_to_write.append(
                f"[$text-primary]Operating on path: {self.op_data.node_data.path}[/]"
            )
        self.update("\n".join(lines_to_write))


class OperateScreenBase(Screen[None], AppType):

    BINDINGS = [
        Binding(
            key="escape",
            action=BindingAction.exit_screen,
            description=BindingDescription.cancel,
        )
    ]

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
