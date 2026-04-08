import time
from asyncio import sleep
from enum import StrEnum
from functools import wraps
from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator

from chezmoi_mousse import CMD, AppType, OpBtnEnum

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from chezmoi_mousse import CommandResult, ReadCmd

__all__ = ["LoadingLabel", "LoadingModal", "min_wait"]


type MinWaitReturn = Callable[..., Awaitable[CommandResult | None]]


def min_wait(func: "Callable[..., Awaitable[None]]") -> MinWaitReturn:
    # not needed for anything else than showing log messages briefly for humans
    @wraps(func)
    async def wrapper(self: "LoadingModal", *args: "OpBtnEnum") -> None:
        min_wait_time = 0.4
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

    @property
    def with_color(self) -> str:
        return f"[$text-primary]{self.value}[/]"


class LoadingModal(ModalScreen[None], AppType):

    label_text: reactive[str | None] = reactive(None, init=False)

    def __init__(self, btn_enum: OpBtnEnum | None) -> None:
        super().__init__()
        self.btn_enum: OpBtnEnum | None = btn_enum

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label(LoadingLabel.loading.with_color)
            yield LoadingIndicator()

    def on_mount(self) -> None:
        if self.btn_enum != OpBtnEnum.reload:
            CMD.changed_paths.clear()
        CMD.loading_modal_results.clear()

    def watch_label_text(self, label_text: str | None) -> None:
        if label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)

    @work
    async def run_all_read_cmds(self) -> None:
        for read_cmd in CMD.refresh_read_cmds:
            await self._run_read_command(read_cmd).wait()

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: "ReadCmd") -> None:
        self.label_text = CMD.run_cmd.review_cmd(verb_cmd=read_cmd)
        cmd_result: CommandResult = CMD.run_cmd.read(read_cmd)
        setattr(CMD.cache.cmd_results, f"{read_cmd.name}", cmd_result)
        CMD.loading_modal_results.append(cmd_result)

    @work(thread=True, exit_on_error=False)
    @min_wait
    async def run_write_command(self, btn_enum: "OpBtnEnum") -> None:
        if btn_enum.path_arg == CMD.cache.dest_dir:
            btn_enum.path_arg = None
        self.label_text = CMD.run_cmd.review_cmd(
            verb_cmd=btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        cmd_result: CommandResult = CMD.run_cmd.perform(
            btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        CMD.loading_modal_results.append(cmd_result)

    @work(thread=True)
    @min_wait
    async def update_changed_paths(self) -> None:
        self.label_text = LoadingLabel.update_changed_and_cached.with_color

        self.old_managed_paths: set[Path] = CMD.cache.sets.managed_paths.copy()
        self.old_status_paths: set[Path] = CMD.cache.sets.status_paths.copy()

        CMD.cache.update_path_sets()

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + per-path
        # status status changes
        new_managed = CMD.cache.sets.managed_paths
        new_status = CMD.cache.sets.status_paths

        removed = self.old_managed_paths - new_managed
        added = new_managed - self.old_managed_paths
        changed_status = {
            p
            for p in (self.old_managed_paths & new_managed)
            if (p in self.old_status_paths) != (p in new_status)
        }

        CMD.added_paths = sorted(added)
        CMD.removed_paths = sorted(removed)
        CMD.changed_status_paths = sorted(changed_status)
        CMD.changed_paths = sorted(removed | added | changed_status)
