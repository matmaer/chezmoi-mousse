from enum import StrEnum

from textual.reactive import reactive
from textual.widgets import Button, Static

from chezmoi_mousse import (
    AppIds,
    AppType,
    Chars,
    CommandResult,
    OpBtnEnum,
    OpBtnLabels,
    OperateStrings,
    TabName,
    Tcss,
)
from chezmoi_mousse.gui.tabs.add_tab import AddTab
from chezmoi_mousse.gui.tabs.apply_tab import ApplyTab
from chezmoi_mousse.gui.tabs.re_add_tab import ReAddTab

__all__ = ["OperateInfo"]


class InfoBorders(StrEnum):
    add_subtitle = f"path on disk {Chars.right_arrow} chezmoi repo"
    apply_subtitle = f"chezmoi repo {Chars.right_arrow} path on disk"
    cmd_output_subtitle = "Command Output"
    destroy_subtitle = (
        f"{Chars.x_mark} delete on disk and in chezmoi repo {Chars.x_mark}"
    )
    error_subtitle = "Operation failed with errors"
    forget_subtitle = (
        f"{Chars.x_mark} leave on disk but remove from chezmoi repo "
        f"{Chars.x_mark}"
    )
    init_subtitle = "Initialize chezmoi repository"
    re_add_subtitle = (
        f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    )
    success_subtitle = "Operation completed successfully"


class OperateInfo(Static, AppType):

    cmd_result: reactive["CommandResult | None"] = reactive(None, init=False)
    btn_enum: reactive["OpBtnEnum | None"] = reactive(None, init=False)

    def __init__(self, *, ids: AppIds) -> None:
        self.ids = ids
        super().__init__(id=self.ids.static.operate_info)

    def watch_cmd_result(self) -> None:
        if self.cmd_result is None:
            return
        self.border_title = InfoBorders.cmd_output_subtitle
        if self.cmd_result.exit_code == 0:
            self.border_subtitle = InfoBorders.success_subtitle
            self.add_class(Tcss.operate_success)
            self.update(f"{self.cmd_result.std_out}")
        else:
            self.border_subtitle = InfoBorders.error_subtitle
            self.add_class(Tcss.operate_error)
            self.update(f"{self.cmd_result.std_err}")

    def run_operate_command(self, *, ids: "AppIds") -> None:
        assert self.btn_enum is not None
        tab_widget = self.screen.query_one(ids.tab_qid)
        if ids.canvas_name == TabName.apply:
            tab_widget = self.query_exactly_one(ApplyTab)
        elif ids.canvas_name == TabName.re_add:
            tab_widget = self.query_exactly_one(ReAddTab)
        elif ids.canvas_name == TabName.add:
            tab_widget = self.query_exactly_one(AddTab)
        else:
            raise ValueError(
                f"write_pre_operate_info called on unsupported tab: "
                f"{ids.canvas_name}"
            )
        if tab_widget.current_node is None:
            raise ValueError("current_node is None in run_operate_command")
        operate_result = self.app.cmd.perform(
            self.btn_enum.write_cmd, path_arg=tab_widget.current_node.path
        )
        if operate_result.dry_run is False:
            close_btn = tab_widget.query_one(tab_widget.ids.close_q, Button)
            close_btn.label = OpBtnLabels.reload

    def write_pre_operate_info(self, *, ids: AppIds) -> None:
        assert self.btn_enum is not None
        lines_to_write: list[str] = []
        tab_widget = self.screen.query_one(ids.tab_qid)
        if ids.canvas_name == TabName.apply:
            tab_widget = self.query_exactly_one(ApplyTab)
        elif ids.canvas_name == TabName.re_add:
            tab_widget = self.query_exactly_one(ReAddTab)
        else:
            raise ValueError(
                f"write_pre_operate_info called on unsupported tab: "
                f"{ids.canvas_name}"
            )
        if tab_widget.current_node is None:
            raise ValueError("current_node is None in write_pre_operate_info")
        lines_to_write.append(
            f"{OperateStrings.ready_to_run}"
            f"[$text-warning]"
            f"{self.btn_enum.write_cmd.pretty_cmd} "
            f"{tab_widget.current_node.path}[/]"
        )
        if self.app.changes_enabled is True:
            if self.app.splash_data is None:
                raise ValueError(
                    "splash_data is None in write_pre_operate_info"
                )
            if self.app.splash_data.parsed_config.git_autocommit is True:
                lines_to_write.append(OperateStrings.auto_commit)
            if self.app.splash_data.parsed_config.git_autopush is True:
                lines_to_write.append(OperateStrings.auto_push)
        operate_info = self.screen.query_one(ids.static.operate_info_q, Static)
        operate_info.update("\n".join(lines_to_write))

    def watch_btn_enum(self) -> None:
        if self.btn_enum is None:
            return
        if self.btn_enum == OpBtnEnum.add:
            self.border_subtitle = InfoBorders.add_subtitle
        elif self.btn_enum == OpBtnEnum.apply:
            self.border_subtitle = InfoBorders.apply_subtitle
        elif self.btn_enum == OpBtnEnum.destroy:
            self.border_subtitle = InfoBorders.destroy_subtitle
        elif self.btn_enum == OpBtnEnum.forget:
            self.border_subtitle = InfoBorders.forget_subtitle
        elif self.btn_enum == OpBtnEnum.re_add:
            self.border_subtitle = InfoBorders.re_add_subtitle
        elif self.btn_enum == OpBtnEnum.init:
            self.border_subtitle = InfoBorders.init_subtitle
