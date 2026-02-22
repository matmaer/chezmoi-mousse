from asyncio import sleep
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse import (
    CMD,
    AppType,
    CommandResult,
    OpBtnEnum,
    OperateString,
    TabName,
    Tcss,
)

from .common.messages import CompletedOpMsg, ProgressTextMsg

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds


__all__ = ["OperateMode"]


class LoadingModal(ModalScreen[None]):

    def __init__(self, ids: "AppIds", *, pretty_cmd: str) -> None:
        super().__init__()
        self.ids = ids
        self.pretty_cmd = pretty_cmd

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Running {self.pretty_cmd}", id=self.ids.label.loading)
            yield LoadingIndicator()

    @on(ProgressTextMsg)
    def update_pretty_cmd_text(self, message: ProgressTextMsg) -> None:
        message.stop()
        label = self.query_one(self.ids.label.loading_q, Label)
        label.update(message.text)


class OperateMode(Vertical, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_mode)
        self.ids = ids
        self.btn_enum: OpBtnEnum | None = None
        self.init_arg: str | None = None
        self.path_arg: "Path | None" = None

    def compose(self) -> ComposeResult:
        yield Static(id=self.ids.static.op_review_info, classes=Tcss.operate_info)
        yield Static(id=self.ids.static.op_result_info, classes=Tcss.operate_info)

    def on_mount(self) -> None:
        self.display = False
        self.result_info = self.query_one(self.ids.static.op_result_info_q, Static)
        self.result_info.display = False
        self.review_info = self.query_one(self.ids.static.op_review_info_q, Static)

    def update_review_info(self, btn_enum: "OpBtnEnum") -> None:
        self.btn_enum = btn_enum
        info_lines: list[str] = []
        cmd_text = (
            f"{OperateString.ready_to_run} "
            f"{self.btn_enum.write_cmd.bold_review_cmd} "
            f"[$text-success bold]{self.path_arg}[/]"
        )
        info_lines.append("\n".join([cmd_text, self.btn_enum.info_strings]))
        if self.ids.canvas_name in (TabName.add, TabName.re_add):
            if self.app.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if self.app.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.review_info.update("\n".join(info_lines))
        self.review_info.border_title = self.btn_enum.info_title
        self.review_info.border_subtitle = self.btn_enum.info_sub_title

    def refresh_review_info(self) -> None:
        if self.btn_enum is not None:
            if self.ids.canvas_name in (TabName.add, TabName.apply, TabName.re_add):
                self.update_review_info(self.btn_enum)

    @work(thread=True)
    def run_perform_command(self, btn_enum: "OpBtnEnum") -> CommandResult:
        return CMD.perform(btn_enum.write_cmd, path_arg=self.path_arg)

    @work(exit_on_error=False)
    async def run_command(self, btn_enum: "OpBtnEnum") -> None:
        pretty_cmd = f"{btn_enum.write_cmd.bold_review_cmd}"
        if self.path_arg is not None:
            pretty_cmd += f"[$text-success bold] {self.path_arg}[/]"
        elif self.init_arg is not None:
            pretty_cmd += f"[$text-success bold] {self.init_arg}[/]"
        loading_modal = LoadingModal(self.ids, pretty_cmd=pretty_cmd)
        await self.app.push_screen(loading_modal)
        worker = self.run_perform_command(btn_enum)
        await worker.wait()
        cmd_result = worker.result
        if cmd_result is None:
            self.notify("Command result is None", severity="error")
            return
        self.review_info.display = False
        result_info = self.query_one(self.ids.static.op_result_info_q, Static)
        result_info.update(
            (f"Command completed with exit code {cmd_result.exit_code}, results:\n")
        )
        self.mount(
            ScrollableContainer(cmd_result.pretty_collapsible), after=result_info
        )
        self.app.post_message(CompletedOpMsg(path_arg=self.path_arg))
        await sleep(1)
        self.result_info.display = True
        loading_modal.dismiss()


class LoadMainScreen(Vertical, AppType):
    pass
