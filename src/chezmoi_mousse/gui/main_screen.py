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
from chezmoi_mousse.debug.debug_tab import DebugTab
from chezmoi_mousse.functions import Commands, min_wait, results_queue
from chezmoi_mousse.str_enums import (
    Chars,
    LoadingLabel,
    NotifyMsg,
    OpBtnLabel,
    ReadCmd,
    TabLabel,
    Tcss,
)

from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.doctor_data import DoctorTable
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import ManagedTree
from .common.messages import (
    CurrentNodeMsg,
    RefreshBtnMsg,
    ReviewBtnMsg,
)
from .common.operate_modal import LoadingModal, OperateModal
from .common.switchers import ViewSwitcher
from .tab_panes import AddTab, ApplyTab, ConfigTab, LogsTab, ReAddTab

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
            yield ApplyTab(store.apply_id)
            yield ReAddTab(store.re_add_id)
            yield AddTab(store.add_id)
            yield LogsTab(store.logs_id)
            yield ConfigTab(store.config_id)
            if "debug" in self.app.features:
                yield DebugTab(store.debug_id)
        yield Footer()

    def on_mount(self) -> None:
        self.doctor_table = self.query_exactly_one(DoctorTable)
        self.app_log = self.query_one(store.logs_id.richlog.app_q, AppLog)
        self.cmd_log = self.query_one(store.logs_id.richlog.cmd_q, CmdLog)
        self.main_tabs = self.query_exactly_one(Tabs)
        self.apply_managed_tree = self.query_one(
            store.apply_id.managed_tree_q, ManagedTree
        )
        self.re_add_managed_tree = self.query_one(
            store.re_add_id.managed_tree_q, ManagedTree
        )
        self.tabbed_content = self.query_exactly_one(TabbedContent)
        self._listen_to_command_results()
        self._first_startup()

    def on_unmount(self) -> None:
        results_queue.shutdown(immediate=True)

    @work(thread=True)
    def _listen_to_command_results(self) -> None:
        while True:
            result: CommandResult = results_queue.get()
            if result.cmd_enum is ReadCmd.doctor:
                self.app.call_from_thread(
                    self.doctor_table.populate_table, result.std_out
                )
            elif result.cmd_enum is ReadCmd.cat_config:
                self.app.call_from_thread(
                    self.query_exactly_one(ConfigTab.CatConfigStatic).update,
                    result.std_out,
                )
            elif result.cmd_enum is ReadCmd.ignored:
                self.app.call_from_thread(
                    self.query_exactly_one(ConfigTab.PrettyIgnored).update,
                    result.std_out,
                )
            elif result.cmd_enum is ReadCmd.template_data:
                self.app.call_from_thread(
                    self.query_exactly_one(ConfigTab.PrettyTemplateData).update,
                    store.parsed_template_data,
                )
            self.app.call_from_thread(self._log_command_result, result)
            results_queue.task_done()

    def _log_command_result(self, result: CommandResult) -> None:
        self.app_log.cmd_result = result
        self.cmd_log.cmd_result = result

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _first_startup(self) -> None:
        self.loading_modal = LoadingModal()
        await self.app.push_screen(self.loading_modal)
        await self._update_managed_trees_loading()
        await self.loading_modal.dismiss()

    #####################
    # UI update workers #
    #####################

    async def _purge_views_cache(self) -> None:
        self.loading_modal.label_text = LoadingLabel.purge_cache
        all_views: Iterator[DiffView | ContentsView | GitLogView] = chain(
            self.query(DiffView).results(),
            self.query(ContentsView).results(),
            self.query(GitLogView).results(),
        )
        for view in all_views:
            view.remove_children()

    @min_wait
    async def _update_managed_trees_loading(self) -> None:
        self.loading_modal.label_text = LoadingLabel.update_trees
        self.apply_managed_tree.update_tree()
        self.apply_managed_tree.refresh()
        self.re_add_managed_tree.update_tree()
        self.re_add_managed_tree.refresh()

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
            store.add_path = msg.path
        elif msg.app_ids.tab_label == TabLabel.apply:
            store.apply_path = msg.path
        elif msg.app_ids.tab_label == TabLabel.re_add:
            store.re_add_path = msg.path
        # Update the border subtitle for the tab buttons in the ViewSwitcher
        if msg.path != store.cfg.dest_dir:
            pretty_path = msg.path.relative_to(store.cfg.dest_dir)
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

    @on(RefreshBtnMsg)
    async def handle_refresh_button(self) -> None:
        self.loading_modal = LoadingModal()
        await self.app.push_screen(self.loading_modal)
        await self.loading_modal.run_managed_commands().wait()
        if store.changed_paths.no_changes:
            self.notify(NotifyMsg.no_managed_changes)
            await self._reload_directory_tree_loading()
            if self.tabbed_content.active == TabLabel.add:
                self.notify(NotifyMsg.add_tab_tree_reloaded)
            await self.loading_modal.dismiss()
            return
        # We have changes, push the OperateModal to show these with a close button
        self.app.push_screen(OperateModal((OpBtnLabel.close,)))
        # Meanwhile we continue updates for the loading modal, which will become visible
        # if the Operate modal is dismissed before this is ready
        await self._update_managed_trees_loading()
        await self._reload_directory_tree_loading()
        await self._purge_views_cache()
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
