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

from chezmoi_mousse import CMD, AppType, OpBtnEnum, ReadCmd

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from chezmoi_mousse import CommandResult

__all__ = ["LoadingLabel", "LoadingModal", "min_wait"]

# not needed for anything else than showing log messages briefly for humans
MIN_WAIT_TIME = 1.5


def min_wait(
    func: "Callable[..., Awaitable[None]]",
) -> "Callable[..., Awaitable[CommandResult | None]]":
    @wraps(func)
    async def wrapper(self: "LoadingModal", *args: "OpBtnEnum") -> None:
        start_time = time.monotonic()
        await func(self, *args)
        elapsed = time.monotonic() - start_time
        if elapsed < MIN_WAIT_TIME:
            await sleep(MIN_WAIT_TIME - elapsed)

    return wrapper


class LoadingLabel(StrEnum):
    update_config_tab = "Update Config tab"
    parse_dump_config = "Parse dump-config output"
    purge_cache = "Purge cached data"
    update_trees = "Update Trees"
    log_cmd_results = "Logging command results"
    update_changed_and_cached = "Update changed paths and cached dir nodes"

    @property
    def with_color(self) -> str:
        return f"[$text-primary bold]{self.value}[/]"


class LoadingModal(ModalScreen[None], AppType):

    label_text: reactive[str | None] = reactive(None)

    def __init__(self, btn_enum: OpBtnEnum | None) -> None:
        super().__init__()
        self.btn_enum: OpBtnEnum | None = btn_enum

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label()
            yield LoadingIndicator()

    def on_mount(self) -> None:
        if self.btn_enum != OpBtnEnum.reload:
            CMD.changed_paths.clear()
        CMD.loading_modal_results.clear()
        self.old_managed_paths: set[Path] = CMD.cache.sets.managed_paths.copy()
        self.old_status_pairs: dict[Path, str] = CMD.cache.status_pairs.copy()

    def watch_label_text(self, label_text: str | None) -> None:
        if label_text is None:
            return
        label = self.query_exactly_one(Label)
        label.update(label_text)

    @work(thread=True)
    @min_wait
    async def run_read_command(self, read_cmd: ReadCmd) -> None:
        pretty_cmd = CMD.run_cmd.review_cmd(global_args=read_cmd.value)
        self.label_text = f"Running {pretty_cmd}"
        cmd_result: CommandResult = CMD.run_cmd.read(read_cmd)
        setattr(CMD.cache, f"{read_cmd.name}", cmd_result)
        CMD.loading_modal_results.append(cmd_result)

    @work(thread=True, exit_on_error=False)
    @min_wait
    async def run_write_command(self, btn_enum: "OpBtnEnum") -> None:
        for_review_cmd = ()
        if btn_enum in self.app.run_btn_enums:
            path_arg = str(btn_enum.path_arg) if btn_enum.path_arg is not None else ""
            for_review_cmd = (*btn_enum.write_cmd.value, path_arg)
        self.label_text = f"Running {CMD.run_cmd.review_cmd(for_review_cmd)})"
        cmd_result: CommandResult = CMD.run_cmd.perform(
            btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        CMD.loading_modal_results.append(cmd_result)

    @work(thread=True)
    @min_wait
    async def update_changed_paths(self) -> None:
        self.label_text = LoadingLabel.update_changed_and_cached.with_color

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + Status changes
        changed_paths = (self.old_managed_paths ^ CMD.cache.sets.managed_paths) | {
            p
            for p in self.old_managed_paths & CMD.cache.sets.managed_paths
            if self.old_status_pairs.get(p) != CMD.cache.status_pairs.get(p)
        }
        CMD.changed_paths = sorted(changed_paths)
