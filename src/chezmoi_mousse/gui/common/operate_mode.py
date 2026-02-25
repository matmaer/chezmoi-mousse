import time
from asyncio import sleep
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse import (
    CMD,
    CMD_RESULTS,
    AppType,
    CommandResult,
    OpBtnEnum,
    OperateString,
    ReadCmd,
    TabName,
    Tcss,
)

from .messages import ProgressTextMsg

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

    btn_enum: reactive[OpBtnEnum | None] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_mode)
        self.ids = ids
        self.init_arg: str | None = None
        self.path_arg: Path | None = None

    def compose(self) -> ComposeResult:
        yield Static(id=self.ids.static.operate_info, classes=Tcss.operate_info)
        yield ScrollableContainer(id=self.ids.container.op_cmd_results)

    def on_mount(self) -> None:
        self.display = False
        self.operate_info = self.query_one(self.ids.static.operate_info_q, Static)
        self.op_results_container = self.query_one(
            self.ids.container.op_cmd_results_q, ScrollableContainer
        )

    def update_review_info(self) -> None:
        if self.btn_enum is None:
            return
        info_lines: list[str] = []
        cmd_text = (
            f"{OperateString.ready_to_run} {self.btn_enum.write_cmd.pretty_cmd} "
            f"[$text-primary bold]{self.path_arg}[/]"
        )
        info_lines.append("\n".join([cmd_text, self.btn_enum.info_strings]))
        if self.ids.canvas_name in (TabName.add, TabName.re_add):
            if self.app.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if self.app.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.operate_info.update("\n".join(info_lines))
        self.operate_info.border_title = self.btn_enum.info_title
        self.operate_info.border_subtitle = self.btn_enum.info_sub_title

    def _update_post_run_info(self, cmd_result: CommandResult) -> None:
        self.operate_info.update(
            (
                f"{cmd_result.pretty_cmd}\n"
                f"Command completed with exit code {cmd_result.exit_code}"
            )
        )
        self.operate_info.border_title = cmd_result.operate_info_title
        self.operate_info.border_subtitle = None

    def watch_btn_enum(self, btn_enum: OpBtnEnum) -> None:
        if btn_enum in OpBtnEnum.review_btn_enums():
            self.update_review_info()
        else:
            self.notify(f"Wrong btn_enum {btn_enum} in watch_btn_enum")

    @work
    async def _run_perform_command(self, btn_enum: OpBtnEnum) -> CommandResult:
        return CMD.perform(btn_enum.write_cmd, path_arg=self.path_arg)

    @work
    async def _update_read_outputs(self) -> None:
        for read_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            cmd_result = CMD.read(read_cmd)
            setattr(CMD_RESULTS, f"{read_cmd.name}", cmd_result)
        self.app.cmd_results.new_results = CMD_RESULTS

    @work(exit_on_error=False)
    async def run_command(self, btn_enum: OpBtnEnum) -> None:
        pretty_cmd = btn_enum.write_cmd.pretty_cmd
        if self.path_arg is not None:
            pretty_cmd += f"[$text-primary bold] {self.path_arg}[/]"
        elif self.init_arg is not None:
            pretty_cmd += f"[$text-primary bold] {self.init_arg}[/]"
        loading_modal = LoadingModal(self.ids, pretty_cmd=pretty_cmd)
        await self.app.push_screen(loading_modal)
        start_time = time.monotonic()
        worker_result = self._run_perform_command(btn_enum)
        await worker_result.wait()
        cmd_result = worker_result.result
        if cmd_result is None:
            raise RuntimeError(f"CommandResult is None for {btn_enum.write_cmd.name}")
        self._update_post_run_info(cmd_result)
        read_cmd_worker = self._update_read_outputs()
        await read_cmd_worker.wait()
        self.op_results_container.mount(cmd_result.pretty_collapsible)
        elapsed = time.monotonic() - start_time
        if elapsed < 1.0:
            await sleep(1.0 - elapsed)
        self.operate_info.display = True
        loading_modal.dismiss()
