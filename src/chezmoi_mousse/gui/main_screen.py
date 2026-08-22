from __future__ import annotations

from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING, ClassVar

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent, Tabs

from chezmoi_mousse import store
from chezmoi_mousse.functions import Commands, min_wait
from chezmoi_mousse.str_enums import (
    Chars,
    LoadingLabel,
    NotifyMsg,
    OpBtnLabel,
    TabLabel,
    Tcss,
)

from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import ManagedTree
from .common.messages import (
    CurrentNodeMsg,
    LogCmdResultMsg,
    RefreshBtnMsg,
    ReviewBtnMsg,
)
from .common.operate_modal import LoadingModal, OperateModal
from .common.switchers import ViewSwitcher
from .tab_panes import AddTab, ApplyTab, ConfigTab, DebugTab, LogsTab, ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = ["MainScreen", "CustomHeader"]


class CustomHeader(Header):
    DRY_MODE: ClassVar[str] = (
        "-  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  -"
    )
    LIVE_MODE: ClassVar[str] = "-  c h e z m o i  m o u s s e  --  l i v e  m o d e  -"

    live_run: reactive[bool] = reactive(False)

    def on_mount(self) -> None:
        self.icon = Chars.burger

    def watch_live_run(self, live_run: bool) -> None:
        if live_run is True:
            self.screen.title = self.LIVE_MODE
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.add_class(Tcss.live_run_color)
        if live_run is False:
            self.screen.title = self.DRY_MODE
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.remove_class(Tcss.live_run_color)


class MainScreen(Screen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:
        yield CustomHeader()

        with Vertical(), TabbedContent():
            yield ApplyTab(self.app.cmattr.apply_id)
            yield ReAddTab(self.app.cmattr.re_add_id)
            yield AddTab(self.app.cmattr.add_id)
            yield LogsTab(self.app.cmattr.logs_id)
            yield ConfigTab(self.app.cmattr.config_id)
            if "debug" in self.app.features:
                yield DebugTab(self.app.cmattr.debug_id)
        yield Footer()

    def on_mount(self) -> None:
        self.app_log = self.query_one(self.app.cmattr.logs_id.richlog.app_q, AppLog)
        self.cmd_log = self.query_one(self.app.cmattr.logs_id.richlog.cmd_q, CmdLog)
        self.main_tabs = self.query_exactly_one(Tabs)
        self.apply_managed_tree = self.query_one(
            self.app.cmattr.apply_id.managed_tree_q, ManagedTree
        )
        self.re_add_managed_tree = self.query_one(
            self.app.cmattr.re_add_id.managed_tree_q, ManagedTree
        )
        self.tabbed_content = self.query_exactly_one(TabbedContent)
        self._first_startup()

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _first_startup(self) -> None:
        self.loading_modal = LoadingModal()
        await self.app.push_screen(self.loading_modal)
        await self._update_managed_trees_loading().wait()
        await self._log_cmd_results_loading(store.splash_results()).wait()
        await self.loading_modal.dismiss()

    #####################
    # UI update workers #
    #####################

    @work
    @min_wait
    async def _log_cmd_results_loading(self, cmd_results: list[CommandResult]) -> None:
        self.loading_modal.label_text = LoadingLabel.log_cmd_results
        self.cmd_log.cmd_results = cmd_results
        self.app_log.cmd_results = cmd_results

    @work
    async def _purge_views_cache(self) -> None:
        self.loading_modal.label_text = LoadingLabel.purge_cache
        all_views: Iterator[DiffView | ContentsView | GitLogView] = chain(
            self.query(DiffView).results(),
            self.query(ContentsView).results(),
            self.query(GitLogView).results(),
        )
        for view in all_views:
            view.remove_children()

    @work
    @min_wait
    async def _update_managed_trees_loading(self) -> None:
        self.loading_modal.label_text = LoadingLabel.update_trees
        self.apply_managed_tree.update_tree()
        self.apply_managed_tree.refresh()
        self.re_add_managed_tree.update_tree()
        self.re_add_managed_tree.refresh()
        # Update FilteredDirTree
        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.reload()
        dir_tree.refresh()

    @work
    @min_wait
    async def _reload_directory_tree_loading(self) -> None:
        self.loading_modal.label_text = LoadingLabel.reload_dir_tree
        # Update FilteredDirTree
        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.reload()
        dir_tree.refresh()

    #####################
    # Message handling  #
    #####################

    @on(CurrentNodeMsg)
    def handle_new_tree_node_selected(self, msg: CurrentNodeMsg) -> None:
        msg.stop()
        # Keep track of selected paths for each tab
        if msg.app_ids.tab_label == TabLabel.add:
            self.app.cmattr.add_path = msg.path
        elif msg.app_ids.tab_label == TabLabel.apply:
            self.app.cmattr.apply_path = msg.path
        elif msg.app_ids.tab_label == TabLabel.re_add:
            self.app.cmattr.re_add_path = msg.path
        # Update the border subtitle for the tab buttons in the ViewSwitcher
        if msg.path != self.app.cmattr.dest_dir:
            pretty_path = msg.path.relative_to(self.app.cmattr.dest_dir)
        else:
            pretty_path = msg.path
        self.query_exactly_one(
            msg.app_ids.container.right_side_q, ViewSwitcher
        ).border_subtitle = f" {pretty_path} "
        # Update diff_view, contents_view, and git_log_view with the new path
        self.query_one(msg.app_ids.container.diff_q, DiffView).show_path = msg.path
        self.query_one(
            msg.app_ids.container.contents_q, ContentsView
        ).show_path = msg.path
        self.query_one(msg.app_ids.container.git_log_q, GitLogView).show_path = msg.path

    @on(LogCmdResultMsg)
    def handle_log_cmd_result_msg(self, msg: LogCmdResultMsg) -> None:
        """Currently used by contents.py, diffs.py, and git_log.py to log command
        results for their respective commands."""
        msg.stop()
        self.app_log.cmd_results = msg.cmd_result
        self.cmd_log.cmd_results = msg.cmd_result

    @on(RefreshBtnMsg)
    async def handle_refresh_button(self) -> None:
        await store.store_current_snapshot()
        self.loading_modal = LoadingModal()
        await self.app.push_screen(self.loading_modal)
        await self.loading_modal.run_managed_commands().wait()
        await store.update_changed_paths()
        if store.changed_paths.no_changes:
            self.notify(NotifyMsg.no_managed_changes)
            await self._reload_directory_tree_loading().wait()
            if self.tabbed_content.active == TabLabel.add:
                self.notify(NotifyMsg.add_tab_tree_reloaded)
            await self.loading_modal.dismiss()
            return
        # We have changes, push the OperateModal to show these with a close button
        self.app.push_screen(OperateModal((OpBtnLabel.close,)))
        # Meanwhile we continue updates for the loading modal, which will become visible
        # if the Operate modal is dismissed before this is ready
        await self._update_managed_trees_loading().wait()
        await self._reload_directory_tree_loading().wait()
        await self._purge_views_cache().wait()
        await self._log_cmd_results_loading(store.managed_cmd_results()).wait()
        self.loading_modal.dismiss()

    @on(ReviewBtnMsg)
    def handle_review_button(self, msg: ReviewBtnMsg) -> None:
        run_btn_label = msg.review_button.btn_label.review_to_run
        dry_run_btn_label = Commands.get_dry_run_btn_label()
        self.app.push_screen(
            OperateModal(
                (
                    dry_run_btn_label,
                    run_btn_label,
                    OpBtnLabel.cancel,
                )
            )
        )
