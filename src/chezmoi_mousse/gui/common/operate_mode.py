import time
from asyncio import sleep
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse import (
    CMD,
    PARSED,
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

# not needed for anything else than making log messages readable for humans
RUN_CMD_WAIT_TIME = 0.4
READ_CMD_WAIT_TIME = 0.2
UPDATE_UI_WAIT_TIME = 0.1


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
    changes_enabled: reactive[bool] = reactive(False, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_mode)
        self.ids = ids
        self.path_arg: Path | None = None

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
        self.operate_info = self.query_one(self.ids.static.operate_info_q, Static)
        self.op_results = self.query_one(
            self.ids.container.op_cmd_results_q, ScrollableContainer
        )

    def watch_btn_enum(self, btn_enum: OpBtnEnum) -> None:
        if btn_enum in OpBtnEnum.review_btn_enums():
            self.update_review_info()
        else:
            self.notify(f"Wrong btn_enum {btn_enum} in watch_btn_enum")

    def update_review_info(self) -> None:
        if self.btn_enum is None or self.path_arg is None:
            return
        info_lines: list[str] = []
        pretty_cmd = CMD.filtered_cmd_str(
            CMD.global_cmd + self.btn_enum.write_cmd.value
        )
        cmd_text = (
            f"{OperateString.ready_to_run} [$text-primary bold]{pretty_cmd} "
            f"{self.path_arg.relative_to(PARSED.dest_dir)}[/]"
        )
        info_lines.append(cmd_text)
        info_lines.append(self.btn_enum.info_string)
        if self.ids.canvas_name in (TabName.add, TabName.re_add):
            if PARSED.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if PARSED.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.operate_info.update("\n".join(info_lines))
        self.operate_info.border_title = self.btn_enum.info_title
        self.operate_info.border_subtitle = self.btn_enum.info_sub_title

    @work
    async def _update_operate_info_post_run(self, cmd_result: CommandResult) -> None:
        start_time = time.monotonic()
        self.loading_modal.post_message(
            ProgressTextMsg(f"[$text-darken-2]Update {self.operate_info.name}[/]")
        )
        self.operate_info.update(
            (
                f"{cmd_result.pretty_cmd}\n"
                f"Command completed with exit code {cmd_result.exit_code}"
            )
        )
        self.operate_info.border_title = cmd_result.operate_info_title
        self.operate_info.border_subtitle = None
        elapsed = time.monotonic() - start_time
        if elapsed < UPDATE_UI_WAIT_TIME:
            await sleep(UPDATE_UI_WAIT_TIME - elapsed)

    @work
    async def _update_command_output(self, cmd_result: CommandResult) -> None:
        start_time = time.monotonic()
        self.loading_modal.post_message(
            ProgressTextMsg(f"[$text-darken-2]Update {self.op_results.name}[/]")
        )
        self.op_results.mount(cmd_result.pretty_collapsible)
        elapsed = time.monotonic() - start_time
        if elapsed < UPDATE_UI_WAIT_TIME:
            await sleep(UPDATE_UI_WAIT_TIME - elapsed)

    @work(thread=True)
    async def _run_perform_command(
        self, btn_enum: OpBtnEnum, pretty_cmd: str
    ) -> CommandResult:
        start_time = time.monotonic()
        self.loading_modal.post_message(
            ProgressTextMsg(f"Running [$text-primary bold]{pretty_cmd}[/]")
        )
        cmd_result = CMD.perform(btn_enum.write_cmd, path_arg=self.path_arg)
        elapsed = time.monotonic() - start_time
        if elapsed < RUN_CMD_WAIT_TIME:
            await sleep(RUN_CMD_WAIT_TIME - elapsed)
        return cmd_result

    @work(thread=True)
    async def _run_read_commands(self) -> None:
        for read_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            start_time = time.monotonic()
            pretty_cmd = CMD.filtered_cmd_str(read_cmd.value)
            self.loading_modal.post_message(ProgressTextMsg(f"Running {pretty_cmd}"))
            cmd_result = CMD.read(read_cmd)
            setattr(PARSED.cmd_results, f"{read_cmd.name}", cmd_result)
            elapsed = time.monotonic() - start_time
            if elapsed < READ_CMD_WAIT_TIME:
                await sleep(READ_CMD_WAIT_TIME - elapsed)
        PARSED.update_parsed_data()

    @work(exit_on_error=False)
    async def run_write_command(self, btn_enum: OpBtnEnum) -> None:
        self.loading_modal = LoadingModal(self.ids)
        pretty_cmd = CMD.filtered_cmd_str(CMD.global_cmd + btn_enum.write_cmd.value)
        rel_path_arg = (
            self.path_arg.relative_to(PARSED.dest_dir) if self.path_arg else ""
        )
        if self.path_arg is not None:
            pretty_cmd += f"[$text-primary bold] {rel_path_arg}[/]"
        await self.app.push_screen(self.loading_modal)
        try:
            run_worker = self._run_perform_command(btn_enum, pretty_cmd)
            await run_worker.wait()
            read_worker = self._run_read_commands()
            await read_worker.wait()
            if run_worker.result is None:
                self.notify(f"CommandResult is None for {btn_enum.write_cmd.name}")
                return
            await self._update_operate_info_post_run(run_worker.result).wait()
            await self._update_command_output(run_worker.result).wait()
            self.operate_info.display = True
        finally:
            self.loading_modal.dismiss()
        await self.op_results.remove_children()
