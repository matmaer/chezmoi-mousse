import time
from asyncio import sleep
from functools import wraps
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse import (
    CMD,
    AppType,
    CommandResult,
    OpBtnEnum,
    OperateString,
    ReadCmd,
    TabName,
    Tcss,
)

from .loggers import AppLog, CmdLog
from .messages import ProgressTextMsg

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from chezmoi_mousse import AppIds, OpBtnEnum

__all__ = ["OperateMode"]

# not needed for anything else than showing log messages briefly for humans
MIN_WAIT_TIME = 0.2


def min_wait(
    func: "Callable[..., Awaitable[None]]",
) -> "Callable[..., Awaitable[None]]":
    @wraps(func)
    async def wrapper(self: "OperateMode", *args: "OpBtnEnum") -> None:
        start_time = time.monotonic()
        await func(self, *args)
        elapsed = time.monotonic() - start_time
        if elapsed < MIN_WAIT_TIME:
            await sleep(MIN_WAIT_TIME - elapsed)

    return wrapper


class LoadingModal(ModalScreen[None]):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__()
        self.ids = ids

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label(id=self.ids.label.loading)
            yield LoadingIndicator()

    @on(ProgressTextMsg)
    def update_pretty_cmd_text(self, message: ProgressTextMsg) -> None:
        message.stop()
        label = self.query_one(self.ids.label.loading_q, Label)
        label.update(f"{message.text}")


class OperateMode(Vertical, AppType):

    btn_enum: reactive[OpBtnEnum | None] = reactive(
        None, init=False, always_update=True
    )

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_mode)
        self.ids = ids
        self.path_arg: Path | None = None
        self.run_cmd_result: CommandResult | None = None
        self.all_cmd_results: list[CommandResult] = []

    @property
    def _global_args(self) -> tuple[str, ...]:
        if self.btn_enum is None:
            return ()
        path_arg = str(self.path_arg) if self.path_arg is not None else ""
        return (*self.btn_enum.write_cmd.value, path_arg)

    def compose(self) -> ComposeResult:
        yield Static(
            id=self.ids.static.operate_info,
            classes=Tcss.operate_info,
            name="operate info",
        )
        yield ScrollableContainer(
            id=self.ids.container.op_cmd_results, name="operate command results"
        )

    def on_mount(self) -> None:
        self.display = False
        self.app_log = self.screen.query_exactly_one(AppLog)
        self.cmd_log = self.screen.query_exactly_one(CmdLog)

    def watch_btn_enum(self, btn_enum: OpBtnEnum) -> None:
        if btn_enum in OpBtnEnum.review_btn_enums():
            self.update_review_info()
        elif btn_enum in OpBtnEnum.run_btn_enums():
            self._run_write_command(btn_enum)
        else:
            self.notify(f"Wrong btn_enum {btn_enum} in watch_btn_enum")

    def update_review_info(self) -> None:
        if self.btn_enum is None:
            return
        op_cmd_results = self.query_one(
            self.ids.container.op_cmd_results_q, ScrollableContainer
        )
        op_cmd_results.remove_children()
        info_lines: list[str] = []
        info_lines.append(CMD.run_cmd.review_cmd(global_args=self._global_args))
        info_lines.append(self.btn_enum.info_string)
        if self.ids.canvas_name in (TabName.add, TabName.re_add):
            if CMD.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        operate_info = self.query_one(self.ids.static.operate_info_q, Static)
        operate_info.update("\n".join(info_lines))
        operate_info.border_title = self.btn_enum.info_title
        operate_info.border_subtitle = self.btn_enum.info_sub_title

    @work
    @min_wait
    async def _update_operate_info_post_run(self) -> None:
        operate_info = self.query_one(self.ids.static.operate_info_q, Static)
        self.loading_modal.post_message(
            ProgressTextMsg(f"[$text-darken-2]Update {operate_info.name}[/]")
        )
        if self.run_cmd_result is None:
            operate_info.update("No command result available")
            return
        operate_info.update(
            f"{self.run_cmd_result.pretty_cmd}\n"
            f"Command completed with exit code {self.run_cmd_result.exit_code}"
        )
        operate_info.border_title = self.btn_enum.info_title if self.btn_enum else None
        operate_info.border_subtitle = (
            self.btn_enum.info_sub_title if self.btn_enum else None
        )

    @work
    @min_wait
    async def _update_command_output(self) -> None:
        op_cmd_results = self.query_one(
            self.ids.container.op_cmd_results_q, ScrollableContainer
        )
        op_cmd_results.remove_children()
        self.loading_modal.post_message(
            ProgressTextMsg(f"[$text-darken-2]Update {op_cmd_results.name}[/]")
        )
        for cmd_result in self.all_cmd_results:
            op_cmd_results.mount(cmd_result.pretty_collapsible)

    @work(thread=True)
    @min_wait
    async def _run_perform_command(self, btn_enum: OpBtnEnum) -> None:
        pretty_cmd = CMD.run_cmd.review_cmd(global_args=self._global_args)
        self.loading_modal.post_message(ProgressTextMsg(f"Running {pretty_cmd}"))
        cmd_result = CMD.run_cmd.perform(btn_enum.write_cmd, path_arg=self.path_arg)
        self.run_cmd_result = cmd_result
        self.all_cmd_results.append(cmd_result)

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        pretty_cmd = CMD.run_cmd.review_cmd(global_args=read_cmd.value)
        self.loading_modal.post_message(ProgressTextMsg(f"Running {pretty_cmd}"))
        cmd_result = CMD.run_cmd.read(read_cmd)
        setattr(CMD.cmd_results, f"{read_cmd.name}", cmd_result)
        self.all_cmd_results.append(cmd_result)

    @work
    async def _run_read_commands(self) -> None:
        for read_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            await self._run_read_command(read_cmd).wait()
        CMD.update_parsed_data()

    @work
    @min_wait
    async def _log_all_cmd_results(self) -> None:
        self.loading_modal.post_message(ProgressTextMsg("Logging command results"))
        self.app_log.info("--- Commands executed in OperateMode ---")
        for cmd_result in self.all_cmd_results:
            self.app_log.log_cmd_result(cmd_result)
            self.cmd_log.log_cmd_result(cmd_result)
        self.app_log.info("--- End of OperateMode commands ---")

    @work(exit_on_error=False)
    async def _run_write_command(self, btn_enum: OpBtnEnum) -> None:
        self.all_cmd_results = []
        self.loading_modal = LoadingModal(self.ids)
        await self.app.push_screen(self.loading_modal)
        await self._run_perform_command(btn_enum).wait()
        await self._run_read_commands().wait()
        await self._update_operate_info_post_run().wait()
        await self._update_command_output().wait()
        await self._log_all_cmd_results().wait()
        self.loading_modal.dismiss()
