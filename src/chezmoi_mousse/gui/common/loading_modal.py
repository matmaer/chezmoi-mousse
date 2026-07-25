from __future__ import annotations

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

from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.cm_types import CommandResult
from chezmoi_mousse.enum_data import OpBtnEnum
from chezmoi_mousse.functions import RunChezmoi

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from chezmoi_mousse.cm_types import ChezmoiGui

__all__ = ["LoadingLabel", "LoadingModal", "min_wait"]


type MinWaitReturn = Callable[..., Awaitable[CommandResult | None]]


def min_wait(func: Callable[..., Awaitable[None]]) -> MinWaitReturn:
    # not needed for anything else than showing log messages briefly for humans
    @wraps(func)
    async def wrapper(self: LoadingModal, *args: OpBtnEnum) -> None:
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


class LoadingModal(ModalScreen[list[CommandResult]]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    label_text: reactive[str | None] = reactive(None, init=False)

    def __init__(self, btn_enum: OpBtnEnum | None) -> None:
        self.btn_enum: OpBtnEnum | None = btn_enum
        self.command_results: list[CommandResult] = []
        super().__init__()

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
    async def run_managed_commands(self) -> None:
        for read_cmd in self.app.cm_attr.read_cmd_groups.managed:
            await self._run_read_command(read_cmd).wait()

    @work
    async def run_write_command(self, btn_enum: OpBtnEnum) -> None:
        await self._run_write_command(btn_enum).wait()
        await self.run_managed_commands().wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        self.command_results.append(RunChezmoi.run(read_cmd, dry_run=False))

    @work(thread=True, exit_on_error=False)
    @min_wait
    async def _run_write_command(self, dry_run: bool, btn_enum: OpBtnEnum) -> None:
        if btn_enum.path_arg == self.app.cm_attr.dest_dir:
            btn_enum.path_arg = None
        self.command_results.append(
            RunChezmoi.run(
                btn_enum.write_cmd, dry_run=dry_run, path_arg=btn_enum.path_arg
            )
        )
