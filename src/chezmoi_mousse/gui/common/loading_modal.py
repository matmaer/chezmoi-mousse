import copy
import time
from asyncio import sleep
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator

from chezmoi_mousse import CMD, AppType, OpBtnEnum, OpBtnLabel, ReadCmd

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from chezmoi_mousse import CommandResult

__all__ = ["LoadingModal", "LoadingModalResult", "min_wait"]

# not needed for anything else than showing log messages briefly for humans
MIN_WAIT_TIME = 1.2


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


@dataclass
class LoadingModalResult:
    changed_paths: list["Path"] = field(default_factory=lambda: [])
    changed_root_paths: list["Path"] = field(default_factory=lambda: [])
    read_cmd_results: list["CommandResult"] = field(default_factory=lambda: [])
    write_cmd_result: "CommandResult | None" = None

    @property
    def all_cmd_results(self) -> list["CommandResult"]:
        if self.write_cmd_result is not None:
            return [self.write_cmd_result] + self.read_cmd_results
        return self.read_cmd_results


class LoadingModal(ModalScreen[LoadingModalResult], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.read_cmds = [
            ReadCmd.managed,
            ReadCmd.status,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ]
        self.btn_enum: OpBtnEnum | OpBtnLabel | None = None
        self.run_btn_enums = OpBtnEnum.run_btn_enums()

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label()
            yield LoadingIndicator()

    def on_mount(self) -> None:
        self.to_return = LoadingModalResult()
        self.label = self.query_exactly_one(Label)
        self.old_cached = copy.deepcopy(CMD.cache)
        self._run_commands(self.btn_enum)

    @property
    def _global_args(self) -> tuple[str, ...]:
        if self.btn_enum is None:
            raise ValueError("btn_enum is None when trying to access global args.")
        if self.btn_enum in self.run_btn_enums:
            path_arg = (
                str(self.btn_enum.path_arg)
                if self.btn_enum.path_arg is not None
                else ""
            )
            return (*self.btn_enum.write_cmd.value, path_arg)
        return ()

    @work
    async def _run_commands(self, btn_enum: "OpBtnEnum | OpBtnLabel | None") -> None:
        self.label = self.query_exactly_one(Label)
        if btn_enum in self.run_btn_enums:
            self.label.update(f"Running {CMD.run_cmd.review_cmd(self._global_args)})")
            await self._run_write_command(btn_enum).wait()
            self.label.update("Running read commands to update cache")
            await self.run_all_read_commands().wait()
        elif btn_enum == OpBtnLabel.refresh_tree:
            self.label.update("Running read commands to update cache")
            await self.run_all_read_commands().wait()
        self.label.update("Updating cached data in CMD singleton")
        self.label.update("Collecting changed paths")
        await self._get_changed_paths().wait()
        self.dismiss(self.to_return)

    @work(thread=True, exit_on_error=False)
    @min_wait
    async def _run_write_command(self, btn_enum: "OpBtnEnum") -> None:
        cmd_result: CommandResult = CMD.run_cmd.perform(
            btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        self.to_return.write_cmd_result = cmd_result

    @work
    async def run_all_read_commands(self) -> None:
        for read_cmd in self.read_cmds:
            pretty_cmd = CMD.run_cmd.review_cmd(global_args=read_cmd.value)
            self.label.update(f"Running {pretty_cmd}")
            self._run_read_command(read_cmd)

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        cmd_result: CommandResult = CMD.run_cmd.read(read_cmd)
        setattr(CMD.cmd_results, f"{read_cmd.name}", cmd_result)
        self.to_return.read_cmd_results.append(cmd_result)

    @work
    @min_wait
    async def _get_changed_paths(self) -> None:
        CMD.update_parsed_data()
        old_status = dict(self.old_cached.status_pairs)

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + Status changes
        changes = (self.old_cached.managed_paths ^ set(CMD.cache.managed_paths)) | {
            p
            for p in self.old_cached.managed_paths & set(CMD.cache.managed_paths)
            if old_status.get(p) != CMD.cache.status_pairs.get(p)
        }
        self.to_return.changed_root_paths = self._get_changed_root_paths(changes)
        self.to_return.changed_paths.extend(sorted(changes))

    def _get_changed_root_paths(self, changed_paths: set["Path"]) -> list["Path"]:
        old_files = set(self.old_cached.managed_file_paths)

        # Parent files to their directories
        all_files = old_files | set(CMD.cache.managed_file_paths)
        dirs = {p.parent if p in all_files else p for p in changed_paths}

        # Reduce to common parents
        simplified: set[Path] = set()
        for path in sorted(dirs, key=lambda p: len(p.parts)):
            if not any(path.is_relative_to(parent) for parent in simplified):
                simplified.add(path)
        return sorted(simplified)
