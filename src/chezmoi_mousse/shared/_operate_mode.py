from enum import StrEnum

from textual.reactive import reactive
from textual.widgets import Static

from chezmoi_mousse import (
    AppIds,
    AppType,
    Chars,
    OpBtnEnum,
    OperateInfoData,
    OperateStrings,
    Tcss,
)

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

    operate_info_data: reactive["OperateInfoData | None"] = reactive(
        None, init=False
    )

    def __init__(self, *, ids: AppIds) -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.static.operate_info, classes=Tcss.operate_info
        )

    def run_operate_command(self, *, ids: "AppIds") -> None:
        assert (
            self.operate_info_data is not None
            and self.operate_info_data.path_arg is not None
        )
        self.app.cmd.perform(
            self.operate_info_data.btn_enum.write_cmd,
            path_arg=self.operate_info_data.path_arg,
        )

    def write_pre_operate_info(self, *, ids: AppIds) -> None:
        assert (
            self.operate_info_data is not None
            and self.operate_info_data.btn_enum is not None
        )
        lines_to_write: list[str] = []
        lines_to_write.append(
            f"{OperateStrings.ready_to_run} "
            f"{self.operate_info_data.btn_enum.write_cmd.pretty_cmd}"
        )
        if self.operate_info_data.init_arg is not None:
            lines_to_write.append(f"{self.operate_info_data.init_arg}")
        elif self.operate_info_data.path_arg is not None:
            lines_to_write.append(f"{self.operate_info_data.path_arg}")
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

    def write_post_operate_info(self) -> None:
        if (
            self.operate_info_data is None
            or self.operate_info_data.cmd_result is None
        ):
            return
        self.border_title = InfoBorders.cmd_output_subtitle
        if self.operate_info_data.cmd_result.exit_code == 0:
            self.border_subtitle = InfoBorders.success_subtitle
            self.add_class(Tcss.operate_success)
            self.update(f"{self.operate_info_data.cmd_result.std_out}")
        else:
            self.border_subtitle = InfoBorders.error_subtitle
            self.add_class(Tcss.operate_error)
            self.update(f"{self.operate_info_data.cmd_result.std_err}")

    def watch_operate_info_data(self) -> None:
        if self.operate_info_data is None:
            return
        if self.operate_info_data.btn_enum == OpBtnEnum.add:
            self.border_subtitle = InfoBorders.add_subtitle
        elif self.operate_info_data.btn_enum == OpBtnEnum.apply:
            self.border_subtitle = InfoBorders.apply_subtitle
        elif self.operate_info_data.btn_enum == OpBtnEnum.destroy:
            self.border_subtitle = InfoBorders.destroy_subtitle
        elif self.operate_info_data.btn_enum == OpBtnEnum.forget:
            self.border_subtitle = InfoBorders.forget_subtitle
        elif self.operate_info_data.btn_enum == OpBtnEnum.re_add:
            self.border_subtitle = InfoBorders.re_add_subtitle
        elif self.operate_info_data.btn_enum == OpBtnEnum.init:
            self.border_subtitle = InfoBorders.init_subtitle
        self.write_pre_operate_info(ids=self.ids)
        self.visible = True
