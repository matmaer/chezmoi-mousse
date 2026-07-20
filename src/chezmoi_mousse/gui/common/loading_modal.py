import time
from asyncio import sleep
from enum import StrEnum
from functools import wraps
from typing import TYPE_CHECKING

from textual import getters, work
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator

from chezmoi_mousse import OpBtnEnum, ReadCmd
from chezmoi_mousse.cm_attributes import ManagedPaths

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from chezmoi_mousse.chezmoi_command import CommandResult
    from chezmoi_mousse.type_checking import ChezmoiGui

__all__ = ["LoadingLabel", "LoadingModal", "min_wait"]


type MinWaitReturn = Callable[..., Awaitable[CommandResult | None]]


def min_wait(func: "Callable[..., Awaitable[None]]") -> MinWaitReturn:
    # not needed for anything else than showing log messages briefly for humans
    @wraps(func)
    async def wrapper(self: "LoadingModal", *args: "OpBtnEnum") -> None:
        min_wait_time = 0.2
        start_time = time.monotonic()
        await func(self, *args)
        elapsed = time.monotonic() - start_time
        if elapsed < min_wait_time:
            await sleep(min_wait_time - elapsed)

    return wrapper


class LoadingLabel(StrEnum):
    loading = "Loading"  # the initial label
    log_cmd_results = "Logging command results"
    purge_cache = "Purge cached data"
    update_changed_and_cached = "Update changed paths and cached dir nodes"
    update_config_tab = "Update Config tab"
    update_trees = "Update Trees"
    update_managed_paths = "Update managed paths"

    @property
    def with_color(self) -> str:
        return f"[$text-primary]{self.value}[/]"


class LoadingModal(ModalScreen[None]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    label_text: reactive[str | None] = reactive(None, init=False)

    def __init__(self, btn_enum: OpBtnEnum | None) -> None:
        super().__init__()
        self.btn_enum: OpBtnEnum | None = btn_enum
        self.cmd_results: list[CommandResult] = []

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label(LoadingLabel.loading.with_color)
            yield LoadingIndicator()

    def on_mount(self) -> None:
        if self.btn_enum != OpBtnEnum.reload:
            self.app.cm_attr.changes.clear_changes()

    def watch_label_text(self, label_text: str | None) -> None:
        if label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)

    @work
    async def run_all_read_cmds(self) -> None:
        for read_cmd in ReadCmd.managed_status_commands():
            await self._run_read_command(read_cmd).wait()
        await self._update_cm_attr().wait()

    @work
    async def run_write_command(self, btn_enum: "OpBtnEnum") -> None:
        await self._run_write_command(btn_enum).wait()
        await self.run_all_read_cmds().wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: "ReadCmd") -> None:
        cmd_result: CommandResult = self.app.cm_attr.command.run(read_cmd)
        self.cmd_results.append(cmd_result)

    @work(thread=True, exit_on_error=False)
    @min_wait
    async def _run_write_command(self, btn_enum: "OpBtnEnum") -> None:
        if btn_enum.path_arg == self.app.cm_attr.cfg.dest_dir:
            btn_enum.path_arg = None
        cmd_result: CommandResult = self.app.cm_attr.command.run(
            btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        self.cmd_results.append(cmd_result)

    @work(thread=True)
    @min_wait
    async def _update_cm_attr(self) -> None:
        self.label_text = LoadingLabel.update_changed_and_cached.with_color

        self.previous_managed_paths: ManagedPaths = self.app.cm_attr.managed_paths
        self.app.cm_attr.update_attributes(
            read_commands=ReadCmd.managed_status_commands()
        )

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set
