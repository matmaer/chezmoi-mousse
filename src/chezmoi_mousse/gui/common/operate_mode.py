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
from .filtered_dir_tree import FilteredDirTree
from .git_log import GitLogView
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
) -> "Callable[..., Awaitable[CommandResult | None]]":
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

    btn_enum: reactive[OpBtnEnum | None] = reactive(None, init=False)

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
        self.git_logs: list[GitLogView] = []
        self.managed_trees: list[ManagedTree] = []
        self.list_trees: list[ListTree] = []
        self.all_changed_paths: list[Path] = []
        self.changed_root_paths: list[Path] = []

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
        self.app_log = self.screen.query_exactly_one(AppLog)
        self.cmd_log = self.screen.query_exactly_one(CmdLog)
        self.contents_views = list(self.screen.query(ContentsView))
        self.diff_views = list(self.screen.query(DiffView))
        self.dir_tree = self.screen.query_exactly_one(FilteredDirTree)
        self.git_logs = list(self.screen.query(GitLogView))
        self.list_trees = list(self.screen.query(ListTree))
        self.log_collapsibles = self.query_one(
            self.ids.container.command_output_q, ScrollableContainer
        )
        self.managed_trees = list(self.screen.query(ManagedTree))
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

    @work(exit_on_error=False)
    @min_wait
    async def _run_write_command(self, btn_enum: OpBtnEnum) -> None:
        self.loading_modal = LoadingModal()
        self.old_cached = None
        await self.app.push_screen(self.loading_modal)
        await self._run_perform_command(btn_enum).wait()
        await self._run_read_commands().wait()
        await self._update_log_collapsibles().wait()
        await self._log_all_cmd_results_to_logs_tab().wait()
        if self.run_cmd_result is not None and self.run_cmd_result.is_dry_run is False:
            await self._update_cached_data_and_trees().wait()
        self.loading_modal.dismiss()

    @work(exit_on_error=False)
    async def _run_read_commands(self) -> None:
        for read_cmd in self.read_commands:
            await self._run_read_command(read_cmd).wait()

    @work
    async def _cleanup_after_operation(self) -> None:
        self.all_cmd_results = []
        self.old_cached = None
        self.changed_root_paths = []
        self.log_collapsibles.remove_children()

    @work
    @min_wait
    async def _update_log_collapsibles(self) -> None:
        self.loading_modal.post_message(
            ProgressTextMsg(f"[$text-darken-2]Update {self.log_collapsibles.name}[/]")
        )
        self.log_collapsibles.mount(
            Label("Command output", classes=Tcss.main_section_label)
        )
        for cmd_result in self.all_cmd_results:
            self.log_collapsibles.mount(cmd_result.pretty_collapsible)
        self.log_collapsibles.mount(
            Label("Changed paths", classes=Tcss.main_section_label)
        )
        if not self.all_changed_paths:
            dry_run = (
                " (dry run)"
                if self.run_cmd_result and self.run_cmd_result.is_dry_run
                else ""
            )
            self.log_collapsibles.mount(Static(f"No paths changed.{dry_run}"))
        for path in self.all_changed_paths:
            self.log_collapsibles.mount(Static(str(path), classes=Tcss.info))

    @work(thread=True)
    @min_wait
    async def _run_perform_command(self, btn_enum: OpBtnEnum) -> None:
        pretty_cmd = CMD.run_cmd.review_cmd(global_args=self._global_args)
        self.loading_modal.post_message(ProgressTextMsg(f"Running {pretty_cmd}"))
        self.run_cmd_result = CMD.run_cmd.perform(
            btn_enum.write_cmd, path_arg=btn_enum.path_arg
        )
        self.all_cmd_results.append(self.run_cmd_result)
        self.operate_info.update(
            f"{self.run_cmd_result.pretty_cmd}\n"
            f"Command completed with exit code {self.run_cmd_result.exit_code}"
        )
        if self.btn_enum is not None:
            self.operate_info.border_title = self.btn_enum.op_info_title
            self.operate_info.border_subtitle = self.btn_enum.op_info_subtitle
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
    async def manual_refresh(self) -> None:
        changes_enabled = bool(CMD.run_cmd.changes_enabled)
        if changes_enabled is False:
            CMD.run_cmd.changes_enabled = True
        self.loading_modal = LoadingModal()
        await self.app.push_screen(self.loading_modal)
        await self._run_read_commands().wait()
        await self._log_all_cmd_results_to_logs_tab().wait()
        await self._update_cached_data_and_trees().wait()
        CMD.run_cmd.changes_enabled = changes_enabled
        if not self.all_changed_paths:
            self.notify("No managed paths changed.", severity="warning")
        else:
            changed_paths = "\n".join(
                sorted(str(path) for path in self.all_changed_paths)
            )
            self.notify(f"Updated trees with changed paths:\n{changed_paths}")
        await self._cleanup_after_operation().wait()
        self.loading_modal.dismiss()

    @work
    @min_wait
    async def _log_all_cmd_results_to_logs_tab(self) -> None:
        self.loading_modal.post_message(ProgressTextMsg("Logging command results"))
        self.app_log.info("--- Commands logged in OperateMode ---")
        for cmd_result in self.all_cmd_results:
            if cmd_result.is_dry_run and cmd_result.cmd_enum in self.read_commands:
                continue
            self.app_log.log_cmd_result(cmd_result)
            self.cmd_log.log_cmd_result(cmd_result)
        self.app_log.info("--- End of OperateMode commands ---")

    @work
    async def _get_changed_root_paths(self, old_cached: CachedData) -> list["Path"]:
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
        self.all_changed_paths = sorted(changes)
        # Parent files to their directories
        all_files = old_files | set(CMD.cache.managed_file_paths)
        dirs = {p.parent if p in all_files else p for p in changes}

        # Reduce to common parents
        simplified: set[Path] = set()
        for path in sorted(dirs, key=lambda p: len(p.parts)):
            if not any(path.is_relative_to(parent) for parent in simplified):
                simplified.add(path)
        self.changed_root_paths = sorted(simplified)
        return sorted(simplified)

    @work
    @min_wait
    async def _update_cached_data_and_trees(self) -> None:
        self.loading_modal.post_message(
            ProgressTextMsg("Updating cached data and trees")
        )
        old_cached = copy.deepcopy(CMD.cache)
        CMD.update_parsed_data()
        changed = await self._get_changed_root_paths(old_cached).wait()
        if not changed:
            return
        for diff_view in self.diff_views:
            diff_view.purge_mounted_containers(changed)
        for contents_view in self.contents_views:
            contents_view.purge_mounted_containers(changed)
        for git_log in self.git_logs:
            git_log.purge_mounted_containers(changed)
        for managed_tree in self.managed_trees:
            managed_tree.populate_tree()
        for list_tree in self.list_trees:
            list_tree.populate_tree()
        self.dir_tree.refresh()
        self.dir_tree.reload()
        self.dir_tree.select_node(self.dir_tree.root)
