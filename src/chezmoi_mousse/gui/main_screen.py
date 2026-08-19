from __future__ import annotations

from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent, Tabs

from chezmoi_mousse.functions import ResultCollector, min_wait
from chezmoi_mousse.str_enums import Chars, LoadingLabel, Tcss

from .common.actionables import (
    DirContentBtn,
    ReviewBtnGroup,
)
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import ManagedTree
from .common.messages import CurrentNodeMsg, LogCmdResultMsg, ReviewBtnMsg
from .common.operate_modal import LoadingModal
from .common.switchers import ViewSwitcher
from .tab_panes import AddTab, ApplyTab, ConfigTab, DebugTab, LogsTab, ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse.dataclass_types import ReviewBtnData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = ["MainScreen", "CustomHeader"]


class CustomHeader(Header):
    dry_run: reactive[bool] = reactive(True)
    dry_run_mode = "-  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  -"
    live_mode = "-  c h e z m o i  m o u s s e  --  l i v e  m o d e  -"

    def on_mount(self) -> None:
        self.icon = Chars.burger

    def watch_dry_run(self, dry_run: bool) -> None:
        if dry_run is False:
            # TODO: check if we can just set screen title
            self.screen.title = self.dry_run_mode
            header_title = self.query_exactly_one("HeaderTitle", Static)
            header_title.add_class(Tcss.live_run_color)
        if dry_run is True:
            self.screen.title = self.live_mode
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
        self._push_loading_modal(run_data=None, first_run=True)

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _push_loading_modal(
        self, run_data: ReviewBtnData | None, first_run: bool = False
    ) -> None:
        self.loading_modal = LoadingModal(run_data=run_data)
        await self.app.push_screen(self.loading_modal)

        results_to_log: list[CommandResult] = []
        if run_data is None:
            await self.loading_modal.run_managed_commands().wait()
        elif first_run:
            results_to_log = ResultCollector.splash_results()
        if run_data is not None:  # either a run or refresh tree button was pressed
            results_to_log.extend(ResultCollector.managed_cmd_results())
            await self._purge_views_cache().wait()
        await self._update_trees().wait()
        await self._log_cmd_results(results_to_log).wait()
        await self.loading_modal.dismiss()

    #####################
    # UI update workers #
    #####################

    @work
    @min_wait
    async def _log_cmd_results(self, cmd_results: list[CommandResult]) -> None:
        self.loading_modal.label_text = LoadingLabel.log_cmd_results
        self.cmd_log.cmd_results = cmd_results
        self.app_log.cmd_results = cmd_results

    @work
    @min_wait
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
    async def _update_trees(self) -> None:
        self.loading_modal.label_text = LoadingLabel.update_trees
        self.apply_managed_tree.update_tree()
        self.apply_managed_tree.refresh()
        self.re_add_managed_tree.update_tree()
        self.re_add_managed_tree.refresh()
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
        # Update the border subtitle for the tab buttons in the ViewSwitcher
        self.query_exactly_one(
            msg.ids.container.right_side_q, ViewSwitcher
        ).border_subtitle = msg.border_path
        # Update diff_view, contents_view, and git_log_view with the new path
        self.query_one(msg.ids.container.diff_q, DiffView).show_path = msg.path
        self.query_one(msg.ids.container.contents_q, ContentsView).show_path = msg.path
        self.query_one(msg.ids.container.git_log_q, GitLogView).show_path = msg.path
        # Set path_arg for the btn_enums for subsequent operations
        self.query_one(
            msg.ids.container.operate_buttons_q, ReviewBtnGroup
        ).set_path_arg(msg.path)

    @on(DirContentBtn.Pressed)
    def handle_path_in_dir_node_pressed(self, event: DirContentBtn.Pressed) -> None:
        if isinstance(event.button, DirContentBtn):
            event.stop()
            _ = self.query_one(event.button.app_ids.managed_tree_q, ManagedTree)
            self.notify(f"Not yet implemented {type(DirContentBtn)}")
            return

    @on(LogCmdResultMsg)
    def handle_log_cmd_result_msg(self, msg: LogCmdResultMsg) -> None:
        """Currently used by contents.py, diffs.py, and git_log.py to log command
        results for their respective commands."""
        msg.stop()
        self.app_log.cmd_results = [msg.cmd_result]
        self.cmd_log.cmd_results = [msg.cmd_result]

    @on(ReviewBtnMsg)
    def handle_review_button(self, msg: ReviewBtnMsg) -> None:
        self.notify(f"Pressed {msg.btn.bd.btn_id}")
