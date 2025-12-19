from typing import TYPE_CHECKING

from textual.widgets import Static

from chezmoi_mousse import AppType, OperateBtn, OperateStrings

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["OperateInfo"]


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
