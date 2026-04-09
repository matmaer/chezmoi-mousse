from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, TabbedContent, TabPane, Tabs

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    CommandResult,
    LogString,
    OpBtnEnum,
    OpBtnLabel,
    TabLabel,
)

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.actionables import OpButton, OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loading_modal import LoadingLabel, LoadingModal, min_wait
from .common.loggers import AppLog, CmdLog
from .common.managed_tree import ManagedTree
from .common.messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg, LogCmdResultMsg
from .common.op_feedback import CommandOutput, OperateInfo, OpFeedBack
from .common.screen_header import CustomHeader
from .common.switchers import ViewSwitcher
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResult

__all__ = ["MainScreen"]


class MainScreen(Screen[None], AppType):

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield OpFeedBack(ids=IDS.main_tabs)

        with Vertical(), TabbedContent():
            yield TabPane(TabLabel.apply, ApplyTab(), id=TabLabel.apply)
            yield TabPane(TabLabel.re_add, ReAddTab(), id=TabLabel.re_add)
            yield TabPane(TabLabel.add, AddTab(), id=TabLabel.add)
            yield TabPane(TabLabel.logs, LogsTab(), id=TabLabel.logs)
            yield TabPane(TabLabel.config, ConfigTab(), id=TabLabel.config)
            yield TabPane(TabLabel.help, HelpTab(), id=TabLabel.help)
            if CMD.dev_mode is True:
                from .debug_tab import DebugTab

                yield TabPane(TabLabel.debug, DebugTab(), id=TabLabel.debug)
        yield Footer()

    def on_mount(self) -> None:
        self.review_btn_enums: set[OpBtnEnum] = OpBtnEnum.review_btn_enums()
        self.run_btn_enums: set[OpBtnEnum] = OpBtnEnum.run_btn_enums()
        self.run_cmd_results: list[CommandResult] = []
        if CMD.dev_mode is True:
            self.notify(LogString.dev_mode_enabled)
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        self.cmd_log = self.query_one(IDS.logs.logger.cmd_q, CmdLog)
        self.main_tabs = self.query_exactly_one(Tabs)
        self.apply_managed_tree = self.query_one(IDS.apply.managed_tree_q, ManagedTree)
        self.re_add_managed_tree = self.query_one(
            IDS.re_add.managed_tree_q, ManagedTree
        )
        self.op_feed_back = self.query_one(
            IDS.main_tabs.container.op_feed_back_q, OpFeedBack
        )
        self.operate_info = self.query_one(
            IDS.main_tabs.static.operate_info_q, OperateInfo
        )
        self.command_output = self.query_one(
            IDS.main_tabs.container.command_output_q, CommandOutput
        )
        self.command_output.display = False
        self._first_time_startup()

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _first_time_startup(self) -> None:
        self.loading_modal = LoadingModal(None)
        await self.app.push_screen(self.loading_modal)
        await self._update_trees().wait()
        await self._log_all_cmd_results(CMD.cache.cmd_results.all).wait()
        await self._update_config_tab().wait()
        self.loading_modal.dismiss()

    @work
    async def _push_loading_modal(self, btn_enum: OpBtnEnum) -> None:
        self.loading_modal = LoadingModal(btn_enum)
        await self.app.push_screen(self.loading_modal)

        if btn_enum in self.run_btn_enums:
            await self.loading_modal.run_write_command(btn_enum).wait()
            await self.operate_info.update_write_cmd_info().wait()
            await self.loading_modal.run_all_read_cmds().wait()
            await self.loading_modal.update_changed_paths().wait()
            await self.command_output.update_cmd_output().wait()
        elif btn_enum == OpBtnEnum.refresh_tree:
            await self.loading_modal.run_all_read_cmds().wait()
            await self.loading_modal.update_changed_paths().wait()
            await self.command_output.update_cmd_output().wait()
            await self._update_trees().wait()
        elif btn_enum == OpBtnEnum.reload:
            if len(CMD.changed_paths) == 0:
                self.notify(
                    "No changed managed paths found, skipping refresh.",
                    severity="warning",
                )
            else:
                self.notify("Changed managed paths found, refreshing data.")
                await self._purge_views_cache().wait()
                await self._update_trees().wait()
        await self._log_all_cmd_results(CMD.loading_modal_results).wait()
        self.loading_modal.dismiss()

    #####################
    # UI update workers #
    #####################

    @work
    @min_wait
    async def _log_all_cmd_results(self, to_log: list["CommandResult | None"]) -> None:
        self.loading_modal.label_text = LoadingLabel.log_cmd_results.with_color
        for cmd_result in to_log:
            if cmd_result is not None:
                self.app_log.log_cmd_result(cmd_result)
                self.cmd_log.log_cmd_result(cmd_result)

    @work
    @min_wait
    async def _purge_views_cache(self) -> None:
        self.loading_modal.label_text = LoadingLabel.purge_cache.with_color
        contents_views = self.query(ContentsView).results()
        diff_views = self.query(DiffView).results()
        git_log_views = self.query(GitLogView).results()
        all_views: Iterator[DiffView | ContentsView | GitLogView] = chain(
            diff_views, contents_views, git_log_views
        )
        for view in all_views:
            view.remove_children()
            view.mounted.clear()

    @work
    @min_wait
    async def _update_config_tab(self) -> None:
        self.loading_modal.label_text = LoadingLabel.update_config_tab.with_color
        config_tab = self.query_exactly_one(ConfigTab)
        config_tab.command_results = CMD.cache

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
        dir_tree.select_node(dir_tree.root)

    #####################
    # Message handling  #
    #####################

    @on(LogCmdResultMsg)
    def _log_cmd_results(self, msg: LogCmdResultMsg) -> None:
        msg.stop()
        self.app_log.log_cmd_result(msg.cmd_result)
        self.cmd_log.log_cmd_result(msg.cmd_result)

    @on(OpButton.Pressed)
    async def handle_operate_btn_msg(self, event: OpButton.Pressed) -> None:
        if not isinstance(event.button, OpButton):
            return
        else:
            event.stop()
        self._set_display(event.button)
        if event.button.btn_enum in self.review_btn_enums:
            self.command_output.reset_widgets()
            self.operate_info.update_review_info(event.button)
            return
        if event.button.btn_enum == OpBtnEnum.reload:
            self.command_output.reset_widgets()
            await self._push_loading_modal(OpBtnEnum.reload).wait()
        elif (
            event.button.btn_enum in self.run_btn_enums
            or event.button.btn_enum == OpBtnEnum.refresh_tree
        ):
            await self._push_loading_modal(event.button.btn_enum).wait()

    @on(CurrentReAddNodeMsg)
    @on(CurrentApplyNodeMsg)
    def handle_new_tree_node_selected(
        self, msg: CurrentApplyNodeMsg | CurrentReAddNodeMsg
    ) -> None:
        msg.stop()
        ids = IDS.apply if isinstance(msg, CurrentApplyNodeMsg) else IDS.re_add

        # Update the border subtitle for the tab buttons in the ViewSwitcher
        tab_buttons = self.query_one(
            ids.container.right_side_q, ViewSwitcher
        ).query_exactly_one(Horizontal)
        tab_buttons.border_subtitle = (
            f" {msg.path} " if msg.path == CMD.cache.dest_dir else f" {msg.path.name} "
        )
        # Update diff_view, contents_view, and git_log_view with the new path
        self.query_one(ids.container.diff_q, DiffView).show_path = msg.path
        self.query_one(ids.container.contents_q, ContentsView).show_path = msg.path
        self.query_one(ids.container.git_log_q, GitLogView).show_path = msg.path
        # Set path_arg for the btn_enums for subsequent operations
        self.query_one(ids.container.operate_buttons_q, OperateButtons).set_path_arg(
            msg.path
        )

        # Could occur at startup or after operations, when we aute select the root node.
        if CMD.cache.sets.no_managed_paths is True:
            for btn_id_q in ids.review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = True
            return
        # Enable/disable all review buttons
        if CMD.cache.sets.contains_status_paths(msg.path) is True:
            for btn_id_q in ids.review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = False
        else:
            for btn_id_q in ids.review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = True
        # Enable/disable Forget and Destroy button
        for btn_id_q in ids.forget_destroy_review_btn_qids:
            if msg.path == CMD.cache.dest_dir:
                self.query_one(btn_id_q, Button).disabled = True
            elif CMD.cache.no_status_paths is False:
                self.query_one(btn_id_q, Button).disabled = False

    ########################
    # Widget display logic #
    ########################

    def _get_set_button_display(self, button: OpButton) -> None:
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
        if button.id in (button.app_ids.op_btn.reload, button.app_ids.op_btn.cancel):
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

    def _set_display(self, button: OpButton) -> None:

        def set_left_side_display(display: bool) -> None:
            left_side = self.query_one(button.app_ids.container.left_side_q, Vertical)
            left_side.display = display

        def set_right_side_display(display: bool) -> None:
            right_side: Vertical | ContentsView | None = None
            if button.app_ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
                right_side = self.query_one(
                    button.app_ids.container.right_side_q, Vertical
                )
            elif button.app_ids.canvas_name == TabLabel.add:
                right_side = self.query_one(
                    button.app_ids.container.contents_q, ContentsView
                )
            else:
                raise NotImplementedError(
                    f"Not implemented for {button.app_ids.canvas_name}"
                )
            right_side.display = display

        def set_switch_slider_display(display: bool) -> None:
            switch_slider = self.query_one(button.app_ids.switch_slider_q, SwitchSlider)
            switch_slider.display = display

        self._get_set_button_display(button)
        if button.btn_enum in (OpBtnEnum.reload, OpBtnEnum.cancel):
            set_left_side_display(True)
            set_right_side_display(True)
            set_switch_slider_display(True)
            self.main_tabs.display = True
            self.op_feed_back.display = False
            self.command_output.display = False
            self.operate_info.display = False
            return
        self.op_feed_back.display = True
        self.main_tabs.display = False
        set_left_side_display(False)
        set_switch_slider_display(False)
        if button.btn_enum in self.review_btn_enums:
            self.command_output.display = False
            self.operate_info.display = True
            set_right_side_display(True)
        elif button.btn_enum in self.run_btn_enums:
            self.command_output.display = True
            self.operate_info.display = True
            set_right_side_display(False)
        elif button.btn_enum == OpBtnEnum.refresh_tree:
            self.command_output.display = True
            self.operate_info.display = False
            set_right_side_display(False)
