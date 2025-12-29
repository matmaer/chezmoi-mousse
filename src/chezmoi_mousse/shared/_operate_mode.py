from enum import StrEnum

from textual.reactive import reactive
from textual.widgets import Static

from chezmoi_mousse import AppIds, Chars, CommandResult, Tcss

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
    re_add_subtitle = (
        f"path on disk {Chars.right_arrow} overwrite chezmoi repo"
    )
    success_subtitle = "Operation completed successfully"


class OperateInfo(Static):

    cmd_result: reactive["CommandResult | None"] = reactive(None, init=False)

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
