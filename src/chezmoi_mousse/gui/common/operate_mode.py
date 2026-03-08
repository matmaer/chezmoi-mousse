import copy
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
    CachedData,
    CommandResult,
    OpBtnEnum,
    OperateString,
    ReadCmd,
    TabLabel,
    Tcss,
)

from .contents import ContentsView
from .diffs import DiffView
from .git_log import GitLog
from .loggers import AppLog, CmdLog
from .messages import ProgressTextMsg
from .trees import ListTree, ManagedTree

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

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Label()
            yield LoadingIndicator()

    @on(ProgressTextMsg)
    def update_pretty_cmd_text(self, message: ProgressTextMsg) -> None:
        message.stop()
        label = self.query_exactly_one(Label)
        label.update(f"{message.text}")


class OperateMode(Vertical, AppType):

    btn_enum: reactive[OpBtnEnum | None] = reactive(
        None, init=False, always_update=True
    )

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.op_mode)
        self.ids = ids
        self.run_cmd_result: CommandResult | None = None
        self.all_cmd_results: list[CommandResult] = []
        self.review_btn_enums: set[OpBtnEnum] = set()
        self.run_btn_enums: set[OpBtnEnum] = set()
        self.read_commands = [
            ReadCmd.managed,
            ReadCmd.status,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ]
        self.diff_views: list[DiffView] = []
        self.contents_views: list[ContentsView] = []
        self.git_logs: list[GitLog] = []
        self.managed_trees: list[ManagedTree] = []
        self.list_trees: list[ListTree] = []
        self.changed_paths: list[Path] = []

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
        self.loading_modal = LoadingModal()
        self.display = False
        self.review_btn_enums = OpBtnEnum.review_btn_enums()
        self.run_btn_enums = OpBtnEnum.run_btn_enums()
        self.app_log = self.screen.query_exactly_one(AppLog)
        self.cmd_log = self.screen.query_exactly_one(CmdLog)
        self.contents_views = list(self.screen.query(ContentsView))
        self.diff_views = list(self.screen.query(DiffView))
        self.git_logs = list(self.screen.query(GitLog))
        self.managed_trees = list(self.screen.query(ManagedTree))
        self.list_trees = list(self.screen.query(ListTree))
        self.op_cmd_results = self.query_one(
            self.ids.container.op_cmd_results_q, ScrollableContainer
        )

    @property
    def _path_arg(self) -> "Path | None":
        return self.btn_enum.path_arg if self.btn_enum is not None else None

    @property
    def _global_args(self) -> tuple[str, ...]:
        if self.btn_enum is None:
            return ()
        path_arg = str(self._path_arg) if self._path_arg is not None else ""
        return (*self.btn_enum.write_cmd.value, path_arg)

    def watch_btn_enum(self, btn_enum: OpBtnEnum) -> None:
        if btn_enum in self.review_btn_enums:
            self.update_review_info()
        elif btn_enum in self.run_btn_enums:
            self._run_write_command(btn_enum)
        else:
            self.notify(f"Wrong btn_enum {btn_enum} in watch_btn_enum")

    def update_review_info(self) -> None:
        if self.btn_enum is None or self.display is False:
            return
        self.op_cmd_results.remove_children()
        info_lines: list[str] = []
        info_lines.append(CMD.run_cmd.review_cmd(global_args=self._global_args))
        info_lines.append(self.btn_enum.op_info_string)
        if self.ids.canvas_name in (TabLabel.add, TabLabel.re_add):
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        operate_info = self.query_one(self.ids.static.operate_info_q, Static)
        operate_info.update("\n".join(info_lines))
        operate_info.border_title = self.btn_enum.op_info_title
        operate_info.border_subtitle = self.btn_enum.op_info_subtitle

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
        operate_info.border_title = (
            self.btn_enum.op_info_title if self.btn_enum else None
        )
        operate_info.border_subtitle = (
            self.btn_enum.op_info_subtitle if self.btn_enum else None
        )

    @work
    @min_wait
    async def _update_command_output(self) -> None:
        self.loading_modal.post_message(
            ProgressTextMsg(f"[$text-darken-2]Update {self.op_cmd_results.name}[/]")
        )
        self.op_cmd_results.mount(
            Label("Command output", classes=Tcss.main_section_label)
        )
        for cmd_result in self.all_cmd_results:
            self.op_cmd_results.mount(cmd_result.pretty_collapsible)
        self.op_cmd_results.mount(
            Label("Changed paths", classes=Tcss.main_section_label)
        )
        if not self.changed_paths:
            dry_run = (
                " (dry run)"
                if self.run_cmd_result and self.run_cmd_result.is_dry_run
                else ""
            )
            self.op_cmd_results.mount(Static(f"No paths changed.{dry_run}"))
        for path in self.changed_paths:
            self.op_cmd_results.mount(Static(str(path)))

    @work(thread=True)
    @min_wait
    async def _run_perform_command(self, btn_enum: OpBtnEnum) -> None:
        pretty_cmd = CMD.run_cmd.review_cmd(global_args=self._global_args)
        self.loading_modal.post_message(ProgressTextMsg(f"Running {pretty_cmd}"))
        cmd_result = CMD.run_cmd.perform(btn_enum.write_cmd, path_arg=self._path_arg)
        self.run_cmd_result = cmd_result
        self.all_cmd_results.append(cmd_result)
        if not cmd_result.is_dry_run:
            self.old_cached = copy.deepcopy(CMD.cache)

    @work(thread=True)
    @min_wait
    async def _run_read_command(self, read_cmd: ReadCmd) -> None:
        pretty_cmd = CMD.run_cmd.review_cmd(global_args=read_cmd.value)
        self.loading_modal.post_message(ProgressTextMsg(f"Running {pretty_cmd}"))
        cmd_result = CMD.run_cmd.read(read_cmd)
        setattr(CMD.cmd_results, f"{read_cmd.name}", cmd_result)
        if cmd_result.is_dry_run:
            return
        self.all_cmd_results.append(cmd_result)

    @work
    async def run_read_commands(self) -> None:
        for read_cmd in self.read_commands:
            await self._run_read_command(read_cmd).wait()

    @work
    async def _get_changed_paths(self, old_cached: CachedData) -> list["Path"]:
        old_managed = set(old_cached.managed_paths)
        old_files = set(old_cached.managed_file_paths)
        old_status = dict(old_cached.status_pairs)

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + Status changes
        changes = (old_managed ^ set(CMD.cache.managed_paths)) | {
            p
            for p in old_managed & set(CMD.cache.managed_paths)
            if old_status.get(p) != CMD.cache.status_pairs.get(p)
        }
        # Parent files to their directories
        all_files = old_files | set(CMD.cache.managed_file_paths)
        dirs = {p.parent if p in all_files else p for p in changes}

        # Reduce to common parents
        simplified: set[Path] = set()
        for path in sorted(dirs, key=lambda p: len(p.parts)):
            if not any(path.is_relative_to(parent) for parent in simplified):
                simplified.add(path)
        self.changed_paths = sorted(simplified)
        return sorted(simplified)

    @work
    @min_wait
    async def update_cached_data(self) -> None:
        self.loading_modal.post_message(ProgressTextMsg("Updating cached data"))
        old_cached = copy.deepcopy(CMD.cache)
        CMD.update_parsed_data()
        changed_paths = await self._get_changed_paths(old_cached).wait()
        if not changed_paths:
            return
        for diff_view in self.diff_views:
            diff_view.update_mounted_containers(changed_paths)
        for contents_view in self.contents_views:
            contents_view.update_mounted_containers(changed_paths)
        for git_log in self.git_logs:
            git_log.remove_all_cached()
        for managed_tree in self.managed_trees:
            managed_tree.populate_tree()
        for list_tree in self.list_trees:
            list_tree.populate_tree()

    @work
    @min_wait
    async def log_all_cmd_results(self) -> None:
        self.loading_modal.post_message(ProgressTextMsg("Logging command results"))
        self.app_log.info("--- Commands executed in OperateMode ---")
        for cmd_result in self.all_cmd_results:
            self.app_log.log_cmd_result(cmd_result)
            self.cmd_log.log_cmd_result(cmd_result)
        self.app_log.info("--- End of OperateMode commands ---")

    @work(exit_on_error=False)
    async def _run_write_command(self, btn_enum: OpBtnEnum) -> None:
        self.all_cmd_results = []
        self.loading_modal = LoadingModal()
        self.old_cached = None
        await self.app.push_screen(self.loading_modal)
        await self._run_perform_command(btn_enum).wait()
        await self._update_operate_info_post_run().wait()
        await self.run_read_commands().wait()
        await self._update_command_output().wait()
        await self.log_all_cmd_results().wait()
        if self.run_cmd_result is not None and self.run_cmd_result.is_dry_run is False:
            await self.update_cached_data().wait()
        self.loading_modal.dismiss()
