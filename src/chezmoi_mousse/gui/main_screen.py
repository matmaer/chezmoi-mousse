from __future__ import annotations

from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING

from textual import getters, on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, TabbedContent, Tabs

from chezmoi_mousse.enum_data import OpBtnEnum, OpBtnLabel
from chezmoi_mousse.str_enums import Chars, TabLabel, Tcss

from .common.actionables import (
    DirContentBtn,
    OpButton,
    OperateButtons,
    SwitchSlider,
    TabButtons,
)
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loading_modal import LoadingLabel, LoadingModal, min_wait
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import ManagedTree
from .common.messages import CurrentNodeMsg, LogCmdResultMsg
from .common.op_feedback import CommandOutput, OperateInfo, OpFeedBack
from .tab_panes import AddTab, ApplyTab, ConfigTab, DebugTab, LogsTab, ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ChezmoiGui, CommandResult

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
        yield OpFeedBack()

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
        self.first_start = True
        self.run_cmd_results: list[CommandResult] = []
        self.app_log = self.query_one(self.app.cmattr.logs_id.richlog.app_q, AppLog)
        self.cmd_log = self.query_one(self.app.cmattr.logs_id.richlog.cmd_q, CmdLog)
        self.main_tabs = self.query_exactly_one(Tabs)
        self.apply_managed_tree = self.query_one(
            self.app.cmattr.apply_id.managed_tree_q, ManagedTree
        )
        self.re_add_managed_tree = self.query_one(
            self.app.cmattr.re_add_id.managed_tree_q, ManagedTree
        )
        self.op_feed_back = self.query_exactly_one(OpFeedBack)
        self.operate_info = self.query_exactly_one(OperateInfo)
        self.command_output = self.query_exactly_one(CommandOutput)
        self.command_output.display = False
        if self.first_start:
            self._first_time_startup()

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _first_time_startup(self) -> None:
        self.loading_modal = LoadingModal(btn_enum=None)
        await self.app.push_screen(self.loading_modal)
        await self._update_trees().wait()
        await self._log_all_cmd_results(
            self.app.cmattr.cmd_results.splash_results_list
        ).wait()
        self.loading_modal.dismiss()
        self._first_start = False

    @work
    async def _push_loading_modal(self, btn_enum: OpBtnEnum) -> None:
        self.loading_modal = LoadingModal(btn_enum=btn_enum)
        await self.app.push_screen(self.loading_modal)

        if btn_enum in OpBtnEnum.run_btn_enums():
            await self.loading_modal.run_write_command(btn_enum).wait()
            await self.command_output.update_cmd_output().wait()
        elif btn_enum == OpBtnEnum.refresh_tree:
            await self.loading_modal.run_managed_commands().wait()
            await self.command_output.update_cmd_output().wait()
            await self._update_trees().wait()
        elif btn_enum == OpBtnEnum.reload:
            if self.app.cmattr.changes.no_changes:
                self.notify(
                    "No changed managed paths found, skipping refresh.",
                    severity="warning",
                )
            else:
                self.notify("Changed managed paths found, refreshing data.")
                await self._purge_views_cache().wait()
                await self._update_trees().wait()
        cmd_results: list[CommandResult] = await self.loading_modal.dismiss()
        await self._log_all_cmd_results(cmd_results).wait()

    #####################
    # UI update workers #
    #####################

    @work
    @min_wait
    async def _log_all_cmd_results(self, cmd_results: list[CommandResult]) -> None:
        self.loading_modal.label_text = LoadingLabel.log_cmd_results.with_color
        for result in cmd_results:
            self.cmd_log.cmd_results = [result]
            self.app_log.cmd_results = [result]

    @work
    @min_wait
    async def _purge_views_cache(self) -> None:
        self.loading_modal.label_text = LoadingLabel.purge_cache.with_color
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
        self.loading_modal.label_text = LoadingLabel.update_trees.with_color
        self.apply_managed_tree.populate_tree()
        self.apply_managed_tree.refresh()
        self.re_add_managed_tree.populate_tree()
        self.re_add_managed_tree.refresh()
        # Update FilteredDirTree
        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.reload()
        dir_tree.refresh()

    #####################
    # Message handling  #
    #####################

    @on(LogCmdResultMsg)
    def _log_cmd_results(self, msg: LogCmdResultMsg) -> None:
        msg.stop()
        self.app_log.cmd_results = [msg.cmd_result]
        self.cmd_log.cmd_results = [msg.cmd_result]

    @on(OpButton.Pressed)
    def handle_operate_btn_msg(self, event: OpButton.Pressed) -> None:
        if not isinstance(event.button, OpButton):
            return
        else:
            event.stop()
        self._set_display(event.button)
        if event.button.btn_enum in OpBtnEnum.review_btn_enums():
            self.command_output.reset_widgets()
            self.operate_info.update_review_info(event.button, self.app.cmattr.dry_run)
            return
        if event.button.btn_enum == OpBtnEnum.reload:
            self.command_output.reset_widgets()
            self._push_loading_modal(OpBtnEnum.reload)
        elif (
            event.button.btn_enum in OpBtnEnum.run_btn_enums()
            or event.button.btn_enum == OpBtnEnum.refresh_tree
        ):
            self._push_loading_modal(event.button.btn_enum)

    @on(DirContentBtn.Pressed)
    def handle_path_in_dir_node_pressed(self, event: DirContentBtn.Pressed) -> None:
        if isinstance(event.button, DirContentBtn):
            event.stop()
            managed_tree = self.query_one(
                event.button.app_ids.managed_tree_q, ManagedTree
            )
            managed_tree.show_requested_node(event.button.path)

    @on(CurrentNodeMsg)
    def handle_new_tree_node_selected(self, msg: CurrentNodeMsg) -> None:
        msg.stop()

        # Update the border subtitle for the tab buttons in the ViewSwitcher
        self.query_exactly_one(
            msg.ids.container.right_side_q, TabButtons
        ).border_subtitle = msg.border_path
        # Update diff_view, contents_view, and git_log_view with the new path
        self.query_one(msg.ids.container.diff_q, DiffView).show_path = msg.path
        self.query_one(msg.ids.container.contents_q, ContentsView).show_path = msg.path
        self.query_one(msg.ids.container.git_log_q, GitLogView).show_path = msg.path
        # Set path_arg for the btn_enums for subsequent operations
        self.query_one(
            msg.ids.container.operate_buttons_q, OperateButtons
        ).set_path_arg(msg.path)

        # always disable all buttons if no managed paths
        if not self.app.cmattr.paths.no_managed_paths:
            for btn_id_q in msg.ids.review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = True

        if msg.no_changed_paths:
            for btn_id_q in (
                b
                for b in msg.ids.review_btn_qids
                if b not in msg.ids.forget_destroy_review_btn_qids
                and not msg.is_dest_dir
            ):
                self.query_one(btn_id_q, Button).disabled = True

        # Enable/disable all review buttons
        if msg.path in self.app.cmattr.paths.managed_dirs:
            for btn_id_q in msg.ids.review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = False
        else:
            for btn_id_q in msg.ids.review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = True
        # Enable/disable Forget and Destroy button, is enabled with or without status
        for btn_id_q in msg.ids.forget_destroy_review_btn_qids:
            if msg.is_dest_dir:
                self.query_one(btn_id_q, Button).disabled = True
            elif not msg.has_status:
                self.query_one(btn_id_q, Button).disabled = False

        # disable apply and re-add review button if no unchanged paths
        if msg.ids.tab_label == TabLabel.apply:
            review_btn = self.query_one(msg.ids.op_btn.apply_review_q, OpButton)
        elif msg.ids.tab_label == TabLabel.re_add:
            review_btn = self.query_one(msg.ids.op_btn.re_add_review_q, OpButton)
        else:
            return
        review_btn.disabled = True

    ########################
    # Widget display logic #
    ########################

    def _set_display(self, button: OpButton) -> None:
        def set_button_display(button: OpButton) -> None:
            op_button_group = self.query_one(
                button.app_ids.container.operate_buttons_q, OperateButtons
            )
            op_buttons: list[OpButton] = [
                b
                for b in op_button_group.query_children().results()
                if isinstance(b, OpButton)
            ]
            reload_btn = self.query_one(button.app_ids.op_btn.reload_q, OpButton)
            cancel_btn = self.query_one(button.app_ids.op_btn.cancel_q, OpButton)
            run_buttons = [b for b in op_buttons if b.id in button.app_ids.run_btn_ids]
            review_buttons = [
                b for b in op_buttons if b.id in button.app_ids.review_btn_ids
            ]
            if button.id in (
                button.app_ids.op_btn.reload,
                button.app_ids.op_btn.cancel,
            ):
                reload_btn.display = False
                cancel_btn.display = False
                for btn in run_buttons:
                    btn.display = False
                for btn in review_buttons:
                    btn.display = True
            elif button in review_buttons:
                for btn in review_buttons:
                    btn.display = False
                for btn in run_buttons:
                    btn.disabled = False
                run_btn_enum = OpBtnEnum.review_to_run(OpBtnLabel(str(button.label)))
                # now lookup the button widget in self.run_buttons with the
                # corresponding enum
                btn_widget: OpButton = next(
                    b for b in run_buttons if b.btn_enum == run_btn_enum
                )
                btn_widget.display = True
                cancel_btn.display = True
            elif button in run_buttons:
                cancel_btn.display = False
                reload_btn.display = True
                button.disabled = True
            elif button.btn_enum == OpBtnEnum.refresh_tree:
                for btn in op_buttons:
                    btn.display = False
                reload_btn.display = True

        def set_left_side_display(display: bool) -> None:
            left_side = self.query_one(button.app_ids.container.left_side_q, Vertical)
            left_side.display = display
            switch_slider = self.query_one(button.app_ids.switch_slider_q, SwitchSlider)
            switch_slider.display = display

        def set_right_side_display(display: bool) -> None:
            right_side: Vertical | ContentsView | None = None
            if button.app_ids.tab_label in (TabLabel.apply, TabLabel.re_add):
                right_side = self.query_one(
                    button.app_ids.container.right_side_q, Vertical
                )
            elif button.app_ids.tab_label == TabLabel.add:
                right_side = self.query_one(
                    button.app_ids.container.contents_q, ContentsView
                )
            else:
                raise NotImplementedError(
                    f"Not implemented for {button.app_ids.tab_label}"
                )
            right_side.display = display

        set_button_display(button)
        if button.btn_enum in (OpBtnEnum.reload, OpBtnEnum.cancel):
            set_left_side_display(True)
            set_right_side_display(True)
            self.main_tabs.display = True
            self.op_feed_back.display = False
            self.command_output.display = False
            self.operate_info.display = False
            return
        self.op_feed_back.display = True
        self.main_tabs.display = False
        set_left_side_display(False)
        if button.btn_enum in OpBtnEnum.review_btn_enums():
            self.command_output.display = False
            self.operate_info.display = True
            set_right_side_display(True)
        elif (
            button.btn_enum in OpBtnEnum.run_btn_enums()
            or button.btn_enum == OpBtnEnum.refresh_tree
        ):
            self.command_output.display = True
            self.operate_info.display = False
            set_right_side_display(False)
