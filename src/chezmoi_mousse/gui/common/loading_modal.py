import time
from asyncio import sleep
from functools import wraps
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator

from chezmoi_mousse import CMD, AppType, OpBtnEnum, ReadCmd

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from chezmoi_mousse import CommandResult

__all__ = ["RefreshModal", "RunCmdModal", "min_wait"]

# not needed for anything else than showing log messages briefly for humans
MIN_WAIT_TIME = 1


def min_wait(
    func: "Callable[..., Awaitable[None]]",
) -> "Callable[..., Awaitable[CommandResult | None]]":
    @wraps(func)
    async def wrapper(self: "RunCmdModal", *args: "OpBtnEnum") -> None:
        start_time = time.monotonic()
        await func(self, *args)
        elapsed = time.monotonic() - start_time
        if elapsed < MIN_WAIT_TIME:
            await sleep(MIN_WAIT_TIME - elapsed)

    return wrapper


class LoadingModalBase(ModalScreen[list["CommandResult"] | None], AppType):

    label_text: reactive[str | None] = reactive(None, init=False)

    READ_CMDS: ClassVar[list[ReadCmd]] = [
        ReadCmd.managed,
        ReadCmd.status,
        ReadCmd.managed_dirs,
        ReadCmd.managed_files,
        ReadCmd.status_dirs,
        ReadCmd.status_files,
    ]

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label()
            yield LoadingIndicator()

    def watch_label_text(self, label_text: str | None) -> None:
        if label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)


class RefreshModal(LoadingModalBase):

    def __init__(self) -> None:
        super().__init__()
        self.btn_enum: OpBtnEnum | None = None
        self.cmd_results: list[CommandResult] = []

    def on_mount(self) -> None:
        self.cmd_results: list[CommandResult] = []

    @work
    async def run_read_commands(self) -> list["CommandResult"]:
        for read_cmd in self.READ_CMDS:
            pretty_cmd = CMD.run_cmd.review_cmd(global_args=read_cmd.value)
            self.label_text = f"Running {pretty_cmd}"
            await self._run_read_command(read_cmd).wait()
        await self._update_changes().wait()
        return self.cmd_results

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        cmd_result: CommandResult = CMD.run_cmd.read(read_cmd)
        setattr(CMD.cache, f"{read_cmd.name}", cmd_result)
        self.cmd_results.append(cmd_result)

    @work(thread=True)
    @min_wait
    async def _update_changes(self) -> None:
        self.label_text = "Updating changed paths and cached dir nodes"
        CMD.update_parsed_data()


class RunCmdModal(RefreshModal):

    def __init__(self) -> None:
        super().__init__()
        self.btn_enum: OpBtnEnum | None = None
        self.cmd_results: list[CommandResult] = []

    def on_mount(self) -> None:
        self.cmd_results: list[CommandResult] = []
        if self.btn_enum is None:
            raise ValueError("btn_enum is None when trying to run commands.")
        self._run_commands(self.btn_enum)

    @property
    def _global_args(self) -> tuple[str, ...] | None:
        if self.btn_enum in self.app.run_btn_enums:
            path_arg = (
                str(self.btn_enum.path_arg)
                if self.btn_enum.path_arg is not None
                else ""
            )
            return (*self.btn_enum.write_cmd.value, path_arg)

    @work
    async def _run_commands(self, btn_enum: "OpBtnEnum") -> None:
        if btn_enum in self.app.run_btn_enums:
            await self._run_write_command(btn_enum).wait()
            await self.run_read_commands().wait()
        elif btn_enum == OpBtnEnum.refresh_tree:
            await self.run_read_commands().wait()
        self.dismiss(self.cmd_results)

    @work(thread=True, exit_on_error=False)
    @min_wait
    async def _run_write_command(self, btn_enum: "OpBtnEnum") -> None:
        if self._global_args is None:
            raise ValueError("Global args are None when trying to run write command.")
        self.label_text = f"Running {CMD.run_cmd.review_cmd(self._global_args)})"
        cmd_result: CommandResult = CMD.run_cmd.perform(
            btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        self.cmd_results.append(cmd_result)
