from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.widgets import Static

from chezmoi_mousse import (
    AppIds,
    AppType,
    OpBtnEnum,
    OpBtnLabels,
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

    def watch_op_btn_enum(self) -> None:
        if self.op_btn_enum is None:
            return
        operate_info_cmd = self.query_one(
            self.ids.static.operate_info_cmd_q, Static
        )
        to_write: list[str] = []
        cmd_text = (
            f"{OperateStrings.ready_to_run} "
            f"{self.op_btn_enum.write_cmd.pretty_cmd} "
            f"[$text-success bold]{self.path_arg}[/]"
        )
        to_write.append(cmd_text)
        if "Add" in self.op_btn_enum.label:
            to_write.append(OperateStrings.add_path_info)
            self.border_subtitle = OperateStrings.add_subtitle
            self.border_title = OpBtnLabels.add_run
        elif "Apply" in self.op_btn_enum.label:
            to_write.append(OperateStrings.apply_path_info)
            self.border_subtitle = OperateStrings.apply_subtitle
            self.border_title = OpBtnLabels.apply_run
        elif "Destroy" in self.op_btn_enum.label:
            to_write.append(OperateStrings.destroy_path_info)
            self.border_subtitle = OperateStrings.destroy_subtitle
            self.border_title = OpBtnLabels.destroy_run
        elif "Forget" in self.op_btn_enum.label:
            to_write.append(OperateStrings.forget_path_info)
            self.border_subtitle = OperateStrings.forget_subtitle
            self.border_title = OpBtnLabels.forget_run
        elif "Re-Add" in self.op_btn_enum.label:
            to_write.append(OperateStrings.re_add_path_info)
            self.border_subtitle = OperateStrings.re_add_subtitle
            self.border_title = OpBtnLabels.re_add_run
        operate_info_cmd.update("\n".join(to_write))
