import copy
import time
from asyncio import sleep
from dataclasses import dataclass, field
from functools import wraps
from typing import TYPE_CHECKING
from textual import work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator, Static

from chezmoi_mousse import (
    CMD,
    AppType,
    OpBtnEnum,
    OperateString,
    ReadCmd,
    TabLabel,
    Tcss,
    OpBtnLabel,
)

from .messages import LoadingResultMsg

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["OperateMode", "LoadingModal", "LoadingModalResult"]

# not needed for anything else than showing log messages briefly for humans
MIN_WAIT_TIME = 1.2


def min_wait(
    func: "Callable[..., Awaitable[None]]",
) -> "Callable[..., Awaitable[CommandResult | None]]":
    @wraps(func)
    async def wrapper(self: "OperateMode", *args: "OpBtnEnum") -> None:
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
        self.run_commands(self.btn_enum)

    @property
    def _global_args(self) -> tuple[str, ...]:
        if self.btn_enum is None:
            raise ValueError("btn_enum is None when trying to access global args.")
        if self.btn_enum == OpBtnLabel.refresh_tree:
            return ()
        elif (
            isinstance(self.btn_enum, OpBtnEnum) and self.btn_enum in self.run_btn_enums
        ):
            path_arg = (
                str(self.btn_enum.path_arg)
                if self.btn_enum.path_arg is not None
                else ""
            )
            return (*self.btn_enum.write_cmd.value, path_arg)
        else:
            raise ValueError(f"Invalid btn_enum {self.btn_enum} in _global_args")

    @work
    async def run_commands(self, btn_enum: "OpBtnEnum | OpBtnLabel | None") -> None:
        self.label = self.query_exactly_one(Label)
        if btn_enum in self.run_btn_enums:
            self.label.update("Running write command")
            await self._run_write_command(btn_enum).wait()
            self.label.update("Running read commands to update cache")
            await self._run_all_read_commands().wait()
        elif btn_enum == OpBtnLabel.refresh_tree:
            self.label.update("Running read commands to update cache")
            await self._run_all_read_commands().wait()
        self.label.update("Updating cached data in CMD singleton")
        await self._update_cached_data().wait()
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
    async def _run_all_read_commands(self) -> None:
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
    async def _update_cached_data(self) -> None:
        CMD.update_parsed_data()

    @work
    @min_wait
    async def _get_changed_paths(self) -> None:
        old_managed = set(self.old_cached.managed_paths)
        old_status = dict(self.old_cached.status_pairs)

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + Status changes
        changes = (old_managed ^ set(CMD.cache.managed_paths)) | {
            p
            for p in old_managed & set(CMD.cache.managed_paths)
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


class OperateMode(Vertical, AppType):

    btn_enum: reactive[OpBtnEnum | None] = reactive(None, init=False)

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_mode)
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Static(
            id=self.ids.static.operate_info,
            classes=Tcss.operate_info,
            name="operate info",
        )
        yield ScrollableContainer(
            id=self.ids.container.command_output, name="operate command results"
        )

    def on_mount(self) -> None:
        self.display = False
        self.log_collapsibles = self.query_one(
            self.ids.container.command_output_q, ScrollableContainer
        )
        self.operate_info = self.query_one(self.ids.static.operate_info_q, Static)
        self.review_btn_enums = OpBtnEnum.review_btn_enums()
        self.run_btn_enums = OpBtnEnum.run_btn_enums()

    @property
    def _global_args(self) -> tuple[str, ...]:
        if self.btn_enum is None:
            raise ValueError("btn_enum is None when trying to access global args.")
        path_arg = (
            str(self.btn_enum.path_arg) if self.btn_enum.path_arg is not None else ""
        )
        return (*self.btn_enum.write_cmd.value, path_arg)

    def watch_btn_enum(self, btn_enum: "OpBtnEnum") -> None:
        if btn_enum.label == OpBtnLabel.reload:
            return
        if btn_enum in self.review_btn_enums:
            self.update_review_info()
        elif btn_enum in self.run_btn_enums:
            loading_modal = LoadingModal()
            loading_modal.btn_enum = btn_enum
            self.app.push_screen(
                loading_modal,
                callback=self.process_loading_modal_result,
                wait_for_dismiss=True,
            )

    def process_loading_modal_result(self, result: "LoadingModalResult | None") -> None:
        if result is None or self.btn_enum is None:
            return
        self.post_message(LoadingResultMsg(loading_result=result))
        self.log_collapsibles.mount(
            Label("Command output", classes=Tcss.main_section_label)
        )
        if result.write_cmd_result is not None:
            self.log_collapsibles.mount(result.write_cmd_result.pretty_collapsible)
        for cmd_result in result.read_cmd_results:
            self.log_collapsibles.mount(cmd_result.pretty_collapsible)
        self.log_collapsibles.mount(
            Label("Changed paths", classes=Tcss.main_section_label)
        )
        if not result.changed_paths:
            dry_run = (
                " (dry run)"
                if result.write_cmd_result and result.write_cmd_result.is_dry_run
                else ""
            )
            self.log_collapsibles.mount(Static(f"No paths changed.{dry_run}"))
        for path in result.changed_paths:
            self.log_collapsibles.mount(Static(str(path), classes=Tcss.info))

        # Update operate info with summary of the operation
        self.operate_info.visible = False
        if result.write_cmd_result is not None:
            self.operate_info.update(
                f"{result.write_cmd_result.full_cmd_filtered}\n"
                f"Command completed with exit code "
                f"{result.write_cmd_result.exit_code}"
            )
            self.operate_info.border_title = self.btn_enum.op_info_title
            self.operate_info.border_subtitle = self.btn_enum.op_info_subtitle
        else:
            self.operate_info.update("Tree refreshed")
            self.operate_info.border_title = "Refresh tree"
            self.operate_info.border_subtitle = (
                "Updated tree with current state of managed paths"
            )
        self.operate_info.visible = True

    def update_review_info(self) -> None:
        if self.btn_enum is None or self.display is False:
            return
        info_lines: list[str] = []
        info_lines.append(CMD.run_cmd.review_cmd(global_args=self._global_args))
        info_lines.append(self.btn_enum.op_info_string)
        if self.ids.canvas_name in (TabLabel.add, TabLabel.re_add):
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.operate_info.update("\n".join(info_lines))
        self.operate_info.border_title = self.btn_enum.op_info_title
        self.operate_info.border_subtitle = self.btn_enum.op_info_subtitle

    # @work
    # async def manual_refresh(self) -> None:
    #     self.loading_modal = LoadingModal()
    #     await self.app.push_screen(self.loading_modal)
    #     # await self._run_read_commands().wait()
    #     await self._log_all_cmd_results_to_logs_tab().wait()
    #     if not self.all_changed_paths:
    #         self.notify("No managed paths changed.", severity="warning")
    #     else:
    #         changed_paths = "\n".join(
    #             sorted(str(path) for path in self.all_changed_paths)
    #         )
    #         self.notify(f"Updated trees with changed paths:\n{changed_paths}")
    #     self.loading_modal.dismiss()
