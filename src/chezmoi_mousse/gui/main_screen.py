from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static, TabbedContent, TabPane, Tabs

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    CommandResult,
    LogString,
    OpBtnEnum,
    OperateString,
    TabLabel,
    Tcss,
)
from chezmoi_mousse._run_cmd import ReadCmd

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.actionables import OpButton, OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loading_modal import RefreshModal, RunCmdModal, min_wait
from .common.loggers import AppLog, CmdLog
from .common.messages import CurrentApplyNodeMsg, CurrentReAddNodeMsg, LogCmdResultMsg
from .common.screen_header import CustomHeader
from .common.switchers import ViewSwitcher
from .common.trees import ListTree, ManagedTree
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["MainScreen", "OperateInfo"]


class OperateInfo(Static, AppType):

    changes_enabled: reactive[bool] = reactive(False, init=False)

    def __init__(self) -> None:
        super().__init__(
            id=IDS.main_tabs.static.operate_info, classes=Tcss.operate_info
        )
        self.btn_enum: OpBtnEnum | None = None

    def on_mount(self) -> None:
        self.display = False

    def update_review_info(self, btn_enum: OpBtnEnum) -> None:
        self.btn_enum = btn_enum
        info_lines: list[str] = []
        path_arg = str(btn_enum.path_arg) if btn_enum.path_arg is not None else ""
        info_lines.append(
            CMD.run_cmd.review_cmd(global_args=(*btn_enum.write_cmd.value, path_arg))
        )
        info_lines.append(btn_enum.op_info_string)
        if IDS.main_tabs.canvas_name in (TabLabel.add, TabLabel.re_add):
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.update("\n".join(info_lines))
        self.border_title = btn_enum.op_info_title
        self.border_subtitle = btn_enum.op_info_subtitle

    def update_post_run_info(
        self, button: OpButton, write_cmd_result: "CommandResult"
    ) -> None:
        cmd_color = (
            "[$text-success]" if write_cmd_result.exit_code == 0 else "[$text-error]"
        )
        cmd = write_cmd_result.full_cmd_filtered
        self.border_title = button.btn_enum.op_info_title
        self.border_subtitle = button.btn_enum.op_info_subtitle
        self.update(f"{cmd_color}{cmd}[/]\nExit code {write_cmd_result.exit_code}")

    def watch_changes_enabled(self) -> None:
        if self.btn_enum is None or not self.display:
            return
        self.update_review_info(self.btn_enum)


class OpFeedBack(Vertical):

    def __init__(self) -> None:
        super().__init__(id=IDS.main_tabs.container.op_feed_back)

    def compose(self) -> ComposeResult:
        yield OperateInfo()
        yield ScrollableContainer(
            id=IDS.main_tabs.container.command_output, name="operate command results"
        )

    def on_mount(self) -> None:
        self.display = False


class MainScreen(Screen[None], AppType):

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield OpFeedBack()

        with Vertical(), TabbedContent():
            yield TabPane(TabLabel.apply, ApplyTab(), id=TabLabel.apply)
            yield TabPane(TabLabel.re_add, ReAddTab(), id=TabLabel.re_add)
            yield TabPane(TabLabel.add, AddTab(), id=TabLabel.add)
            yield TabPane(TabLabel.logs, LogsTab(), id=TabLabel.logs)
            yield TabPane(TabLabel.config, ConfigTab(), id=TabLabel.config)
            yield TabPane(TabLabel.help, HelpTab(), id=TabLabel.help)
            if self.app.dev_mode is True:
                from .debug_tab import DebugTab

                yield TabPane(TabLabel.debug, DebugTab(), id=TabLabel.debug)
        yield Footer()

    def on_mount(self) -> None:
        self.run_cmd_results: list[CommandResult] = []
        if self.app.dev_mode is True:
            self.notify(LogString.dev_mode_enabled)
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        self.cmd_log = self.query_one(IDS.logs.logger.cmd_q, CmdLog)
        self.main_tabs = self.query_exactly_one(Tabs)
        self.op_feed_back = self.query_one(
            IDS.main_tabs.container.op_feed_back_q, Vertical
        )
        self.operate_info = self.query_one(
            IDS.main_tabs.static.operate_info_q, OperateInfo
        )
        self.command_output = self.query_one(
            IDS.main_tabs.container.command_output_q, ScrollableContainer
        )
        self.command_output.display = False
        self._push_refresh_modal(None, CMD.cmd_results.executed_commands)

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _push_refresh_modal(
        self, btn_enum: OpBtnEnum | None, cmd_results: list[CommandResult]
    ) -> None:
        self.refresh_modal = RefreshModal()
        await self.app.push_screen(self.refresh_modal)
        await self._run_refresh_commands(btn_enum, cmd_results).wait()

    @work
    async def _push_run_cmd_modal(self, button: OpButton) -> None:
        self.run_cmd_modal = RunCmdModal()
        self.run_cmd_modal.btn_enum = button.btn_enum

        async def _run_cmd_modal_callback(
            results: "list[CommandResult] | None",
        ) -> None:
            if results is None:
                raise ValueError("results is None in _run_cmd_modal_callback.")
            await self._update_op_feedback(button, results)
            self.run_cmd_results = results

        await self.app.push_screen(
            self.run_cmd_modal, callback=_run_cmd_modal_callback, wait_for_dismiss=True
        )

    async def _update_op_feedback(
        self, button: OpButton, results: "list[CommandResult]"
    ) -> None:
        self.operate_info.update_post_run_info(button, results[0])
        self.command_output.mount(
            Label("Command output", classes=Tcss.main_section_label)
        )
        for cmd_result in results:
            self.command_output.mount(cmd_result.pretty_collapsible)
        self.command_output.mount(
            Label("Changed paths", classes=Tcss.main_section_label)
        )
        if not CMD.changed_paths:
            dry_run = (
                " (dry run)"
                if any(cmd_result.is_dry_run for cmd_result in results)
                else ""
            )
            self.command_output.mount(Static(f"No paths changed.{dry_run}"))
        else:
            for path in CMD.changed_paths:
                self.command_output.mount(Static(str(path), classes=Tcss.info))

    ########################
    # RefreshModal methods #
    ########################

    @work
    @min_wait
    async def _update_config_tab(self, cmd_results: list["CommandResult"]) -> None:
        if ReadCmd.cat_config in [cmd_result.cmd_enum for cmd_result in cmd_results]:
            self.refresh_modal.label_text = "Update Config tab"
            config_tab = self.query_exactly_one(ConfigTab)
            config_tab.command_results = CMD.cmd_results

    @work
    async def _run_refresh_commands(
        self, btn_enum: OpBtnEnum | None, cmd_results: list[CommandResult]
    ) -> None:
        if btn_enum is None:
            await self._update_config_tab(cmd_results).wait()
        await self._purge_views_cache().wait()
        await self._log_all_cmd_results(cmd_results).wait()
        await self._update_trees().wait()
        self.refresh_modal.dismiss()

    @work
    @min_wait
    async def _log_all_cmd_results(self, to_log: "list[CommandResult]") -> None:
        self.refresh_modal.label_text = "Logging command results"
        for cmd_result in to_log:
            self.app_log.log_cmd_result(cmd_result)
            self.cmd_log.log_cmd_result(cmd_result)

    @work
    @min_wait
    async def _purge_views_cache(self) -> None:
        self.refresh_modal.label_text = "Purge cached data"
        contents_views = list(self.query(ContentsView))
        diff_views = list(self.query(DiffView))
        git_log_views = list(self.query(GitLogView))
        for view in diff_views + contents_views + git_log_views:
            view.purge_mounted_containers()

    @work
    @min_wait
    async def _update_trees(self) -> None:
        self.refresh_modal.label_text = "Update Trees"
        list_trees = list(self.query(ListTree))
        managed_trees = list(self.query(ManagedTree))
        for tree in list_trees + managed_trees:
            tree.populate_tree()
        # Update FilteredDirTree
        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.reload()
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
            raise TypeError(f"Expected OpButton, got {type(event.button)}")
        self._set_display(event.button)
        if event.button.btn_enum == OpBtnEnum.reload:
            self.command_output.remove_children()
            await self._push_refresh_modal(
                OpBtnEnum.reload, self.run_cmd_results
            ).wait()
        elif event.button.btn_enum in self.app.review_btn_enums:
            self.operate_info.update_review_info(event.button.btn_enum)
        elif event.button.btn_enum in self.app.run_btn_enums:
            await self._push_run_cmd_modal(event.button).wait()
        elif event.button.btn_enum == OpBtnEnum.refresh_tree:
            await self._push_refresh_modal(
                OpBtnEnum.refresh_tree, self.run_cmd_results
            ).wait()

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
            f" {CMD.cache.dest_dir} "
            if msg.path == CMD.cache.dest_dir
            else f" {msg.path.name} "
        )
        # Update diff_view, contents_view, and git_log_view with the new path
        self.query_one(ids.container.diff_q, DiffView).show_path = msg.path
        self.query_one(ids.container.contents_q, ContentsView).show_path = msg.path
        self.query_one(ids.container.git_log_q, GitLogView).show_path = msg.path
        # Set path_arg for the btn_enums for subsequent operations
        self.query_one(ids.container.operate_buttons_q, OperateButtons).set_path_arg(
            msg.path
        )
        # disable/enable review buttons for file nodes
        if msg.path in CMD.cache.managed_file_paths:
            has_status = msg.path in CMD.cache.status_paths
            self.query_one(ids.tab_operation_btn_q, Button).disabled = not has_status
            for btn_id_q in ids.forget_destroy_review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = not has_status
        elif msg.path in CMD.cache.managed_dirs_with_dest_dir:
            if msg.path == CMD.cache.dest_dir:
                for btn_id_q in ids.forget_destroy_review_btn_qids:
                    self.query_one(btn_id_q, Button).disabled = True
                if CMD.cmd_results.no_status_paths is True:
                    self.query_one(ids.tab_operation_btn_q, Button).disabled = True
            else:
                for btn_id_q in ids.forget_destroy_review_btn_qids:
                    self.query_one(btn_id_q, Button).disabled = False
                self.query_one(ids.tab_operation_btn_q, Button).disabled = bool(
                    msg.path not in CMD.cache.status_paths
                    and msg.path not in CMD.cache.x_dirs_with_status_children
                )

    ########################
    # Widget display logic #
    ########################

    def _get_set_left_side_display(self, ids: "AppIds", display: bool) -> None:
        left_side = self.query_one(ids.container.left_side_q, Vertical)
        left_side.display = display

    def _get_set_right_side_display(self, ids: "AppIds", display: bool) -> None:
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            right_side = self.query_one(ids.container.right_side_q, Vertical)
        elif ids.canvas_name == TabLabel.add:
            right_side = self.query_one(ids.container.contents_q, ContentsView)
        else:
            raise NotImplementedError(f"Not implemented for {ids.canvas_name}")
        right_side.display = display

    def _get_set_switch_slider_display(self, display: bool) -> None:
        switch_slider: SwitchSlider | None = self.app.get_switch_slider_widget()
        if switch_slider is not None:
            switch_slider.display = display

    def _set_display(self, button: OpButton) -> None:
        if button.btn_enum in self.app.review_btn_enums:
            self.op_feed_back.display = True
            self.command_output.display = False
            self.operate_info.display = True
            self.main_tabs.display = False
            self._get_set_left_side_display(button.app_ids, False)
            self._get_set_right_side_display(button.app_ids, True)
            self._get_set_switch_slider_display(False)
        elif (
            button.btn_enum in self.app.run_btn_enums
            or button.btn_enum == OpBtnEnum.refresh_tree
        ):
            self.op_feed_back.display = True
            self.command_output.display = True
            self.operate_info.display = True
            self.main_tabs.display = False
            self._get_set_left_side_display(button.app_ids, False)
            self._get_set_right_side_display(button.app_ids, False)
            self._get_set_switch_slider_display(False)
        elif button.btn_enum in (OpBtnEnum.cancel, OpBtnEnum.reload):
            self.main_tabs.display = True
            self._get_set_left_side_display(button.app_ids, True)
            self._get_set_right_side_display(button.app_ids, True)
            self._get_set_switch_slider_display(True)
            self.op_feed_back.display = False
            self.command_output.display = False
            self.operate_info.display = False
        else:
            raise NotImplementedError(
                f"Display logic not implemented for {button.label}"
            )
