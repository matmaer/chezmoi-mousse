from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.widgets import Static

from chezmoi_mousse import (
    AppIds,
    AppType,
    OpBtnEnum,
    OperateStrings,
    TabName,
    Tcss,
)

__all__ = ["OperateInfo"]


class OperateInfo(VerticalGroup, AppType):

    op_btn_enum: reactive["OpBtnEnum | None"] = reactive(None, init=False)

    def __init__(self, *, ids: AppIds) -> None:
        super().__init__(
            id=ids.container.operate_info, classes=Tcss.operate_info
        )
        self.ids = ids
        self.path_arg: "str | None" = None

    def compose(self) -> ComposeResult:
        yield VerticalGroup(
            Static(id=self.ids.static.operate_info_cmd),
            id=self.ids.container.operate_info,
        )

    def on_mount(self) -> None:
        self.display = False
        if self.ids.canvas_name in (TabName.add, TabName.re_add):
            if self.app.git_auto_commit is True:
                self.mount(Static(OperateStrings.auto_commit))
            if self.app.git_auto_push is True:
                self.mount(Static(OperateStrings.auto_push))

    def update_review_info(self, btn_enum: "OpBtnEnum") -> None:
        info_static = self.query_one(
            self.ids.static.operate_info_cmd_q, Static
        )
        cmd_text = (
            f"{OperateStrings.ready_to_run} "
            f"{btn_enum.write_cmd.pretty_cmd} "
            f"[$text-success bold]{self.path_arg}[/]"
        )
        info_static.update("\n".join([cmd_text, btn_enum.info_strings]))
        self.border_title = btn_enum.info_title
        self.border_subtitle = btn_enum.info_sub_title
