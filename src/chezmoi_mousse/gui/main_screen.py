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
    LogString,
    OpBtnEnum,
    OpBtnLabel,
    OperateString,
    TabLabel,
    Tcss,
)

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.actionables import OpButton, OperateButtons, SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loading_modal import LoadingModal, LoadingModalResult, min_wait
from .common.loggers import AppLog, CmdLog
from .common.messages import (
    CurrentApplyNodeMsg,
    CurrentReAddNodeMsg,
    LoadingResultMsg,
    LogCmdResultMsg,
)
from .common.screen_header import CustomHeader
from .common.switchers import TreeSwitcher, ViewSwitcher
from .common.trees import ListTree, ManagedTree
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["MainScreen"]


class MainScreen(Screen[None], AppType):

    btn_enum: reactive[OpBtnEnum | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__()
        self.last_loading_result: LoadingModalResult = LoadingModalResult()

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        with Vertical(id=IDS.main_tabs.container.op_mode):
            yield Static(
                id=IDS.main_tabs.static.operate_info,
                classes=Tcss.operate_info,
                name="operate info",
            )
            yield ScrollableContainer(
                id=IDS.main_tabs.container.command_output,
                name="operate command results",
            )

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
        self.query_exactly_one(ConfigTab).command_results = CMD.cmd_results
        self.tabs = self.query_exactly_one(Tabs)
        self.command_output = self.query_one(
            IDS.main_tabs.container.op_mode_q, Vertical
        )
        self.command_output.display = False
        self.operate_info = self.query_one(IDS.main_tabs.static.operate_info_q, Static)
        self.command_output = self.query_one(IDS.main_tabs.container.command_output_q)
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        self.cmd_log = self.query_one(IDS.logs.logger.cmd_q, CmdLog)
        if self.app.dev_mode is True:
            self.notify(LogString.dev_mode_enabled)
        self.app_log.write_ready("Commands executed in loading screen")
        for cmd in CMD.cmd_results.executed_commands:
            self.log_cmd_result(cmd)
        self.app_log.write_ready("End of loading screen commands")
        self.list_trees = list(self.query(ListTree))
        self.managed_trees = list(self.query(ManagedTree))
        for tree in self.list_trees + self.managed_trees:
            tree.populate_tree()
        self.contents_views = list(self.query(ContentsView))
        self.diff_views = list(self.query(DiffView))
        self.git_logs = list(self.query(GitLogView))

    def log_cmd_result(self, command_result: "CommandResult") -> None:
        self.app_log.cmd_result = command_result
        self.cmd_log.cmd_result = command_result

    ###################
    # Operate helpers #
    ###################

    def _get_left_side(self, ids: "AppIds") -> TreeSwitcher | Vertical:
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            left_side = self.query_one(ids.container.left_side_q, TreeSwitcher)
        elif ids.canvas_name == TabLabel.add:
            left_side = self.query_one(ids.container.left_side_q, Vertical)
        else:
            raise NotImplementedError(f"Not implemented for {ids.canvas_name}")
        return left_side

    def _get_right_side(self, ids: "AppIds") -> ViewSwitcher | ContentsView:
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            right_side = self.query_one(ids.container.right_side_q, ViewSwitcher)
        elif ids.canvas_name == TabLabel.add:
            right_side = self.query_one(ids.container.contents_q, ContentsView)
        else:
            raise NotImplementedError(f"Not implemented for {ids.canvas_name}")
        return right_side

    def _set_review_display(self, op_button: OpButton) -> None:
        self.tabs.display = False
        self._get_left_side(op_button.app_ids).display = False
        switch_slider: SwitchSlider | None = self.app.get_switch_slider_widget()
        self.command_output.display = False
        if switch_slider is not None:
            switch_slider.display = False

    def _set_post_run_display(self, ids: "AppIds") -> None:
        self._get_right_side(ids).display = False

    def _set_refresh_tree_display(self, ids: "AppIds") -> None:
        self.tabs.display = False
        self._get_left_side(ids).display = False
        self._get_right_side(ids).display = False
        self.tabs.display = False
        switch_slider: SwitchSlider | None = self.app.get_switch_slider_widget()
        if switch_slider is not None:
            switch_slider.display = False

    def _restore_display(self, ids: "AppIds") -> None:
        self.tabs.display = True
        self._get_left_side(ids).display = True
        self._get_right_side(ids).display = True
        switch_slider: SwitchSlider | None = self.app.get_switch_slider_widget()
        if switch_slider is not None:
            switch_slider.display = True

    def _process_loading_modal_result(
        self, result: "LoadingModalResult | None"
    ) -> None:
        if result is None or self.btn_enum is None:
            raise ValueError(
                "Result or btn_enum is None in _process_loading_modal_result."
            )
        self.post_message(LoadingResultMsg(loading_result=result))
        self.command_output.mount(
            Label("Command output", classes=Tcss.main_section_label)
        )
        if result.write_cmd_result is not None:
            self.command_output.mount(result.write_cmd_result.pretty_collapsible)
        for cmd_result in result.read_cmd_results:
            self.command_output.mount(cmd_result.pretty_collapsible)
        self.command_output.mount(
            Label("Changed paths", classes=Tcss.main_section_label)
        )
        if not result.changed_paths:
            dry_run = (
                " (dry run)"
                if result.write_cmd_result and result.write_cmd_result.is_dry_run
                else ""
            )
            self.command_output.mount(Static(f"No paths changed.{dry_run}"))
        for path in result.changed_paths:
            self.command_output.mount(Static(str(path), classes=Tcss.info))

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
        # If this was a refresh-only operation, clear the btn_enum so that
        # pressing the Refresh Trees button again will trigger the watcher.
        if self.btn_enum == OpBtnEnum.refresh_tree:
            self.btn_enum = None

    @work
    @min_wait
    async def _log_loading_cmd_results(
        self, cmd_results: list["CommandResult"]
    ) -> None:
        for cmd_result in cmd_results:
            self.log_cmd_result(cmd_result)

    @work
    @min_wait
    async def _update_trees(self, changed: list["Path"]) -> None:
        for view in self.diff_views + self.contents_views + self.git_logs:
            view.purge_mounted_containers(changed)
            view.show_path = CMD.cache.dest_dir
        for managed_tree in self.managed_trees:
            managed_tree.populate_tree()
            managed_tree.select_node(managed_tree.root)
        for list_tree in self.list_trees:
            list_tree.populate_tree()
            list_tree.select_node(list_tree.root)
        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.refresh()
        dir_tree.reload()
        dir_tree.select_node(dir_tree.root)

    @work
    async def _handle_reload_button(self) -> None:
        self.command_output.remove_children()
        loading_modal = LoadingModal()
        await self.app.push_screen(loading_modal, wait_for_dismiss=True)
        label = loading_modal.query_exactly_one(Label)
        label.update("logging result to app and cmd log")
        await self._log_loading_cmd_results(
            self.last_loading_result.all_cmd_results
        ).wait()
        label.update("updating trees")
        await self._update_trees(self.last_loading_result.changed_paths).wait()

    ############################
    # Message handling methods #
    ############################

    @on(OpButton.Pressed)
    def handle_operate_btn_msg(self, event: OpButton.Pressed) -> None:
        if not isinstance(event.button, OpButton):
            return
        if event.button.btn_enum in (OpBtnLabel.cancel, OpBtnLabel.reload):
            self.command_output.display = False
            self.command_output.remove_children()
            self._restore_display(event.button.app_ids)
            if event.button.btn_enum == OpBtnLabel.reload:
                self._handle_reload_button()
        elif event.button.btn_enum in OpBtnEnum.review_btn_enums():
            self.command_output.display = True
            self.btn_enum = event.button.btn_enum
            self._set_review_display(event.button)
        elif event.button.btn_enum in OpBtnEnum.run_btn_enums():
            self.btn_enum = event.button.btn_enum
            self._set_post_run_display(event.button.app_ids)
        elif event.button.btn_enum == OpBtnEnum.refresh_tree:
            self.btn_enum = OpBtnEnum.refresh_tree

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
        operate_buttons = self.query_one(
            ids.container.operate_buttons_q, OperateButtons
        )
        operate_buttons.set_path_arg(msg.path)
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

    @on(LogCmdResultMsg)
    def log_new_cmd_result(self, msg: LogCmdResultMsg) -> None:
        msg.stop()
        self.log_cmd_result(msg.cmd_result)

    def update_review_info(self) -> None:
        if (
            self.btn_enum is None
            or self.operate_info.display is False
            or self.btn_enum == OpBtnEnum.refresh_tree
        ):
            return
        info_lines: list[str] = []
        if self.btn_enum in self.app.run_btn_enums | self.app.review_btn_enums:
            path_arg = (
                str(self.btn_enum.path_arg)
                if self.btn_enum.path_arg is not None
                else ""
            )
        else:
            path_arg = ""
        info_lines.append(
            CMD.run_cmd.review_cmd(
                global_args=(*self.btn_enum.write_cmd.value, path_arg)
            )
        )
        info_lines.append(self.btn_enum.op_info_string)
        if IDS.main_tabs.canvas_name in (TabLabel.add, TabLabel.re_add):
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.operate_info.update("\n".join(info_lines))
        self.operate_info.border_title = self.btn_enum.op_info_title
        self.operate_info.border_subtitle = self.btn_enum.op_info_subtitle

    @on(LoadingResultMsg)
    async def handle_changed_root_paths(self, msg: LoadingResultMsg) -> None:
        msg.stop()
        if msg.loading_result.changed_root_paths:
            self.notify(
                f"Changed root paths:\n"
                f"{'\n'.join(str(p) for p in msg.loading_result.changed_root_paths)}"
            )
        else:
            self.notify("No root paths were changed.")
        self.last_loading_result = msg.loading_result
        await self._log_loading_cmd_results(
            self.last_loading_result.all_cmd_results
        ).wait()
        await self._update_trees(self.last_loading_result.changed_paths).wait()

    def watch_btn_enum(self, btn_enum: "OpBtnEnum | None") -> None:
        if btn_enum is None:
            return
        if btn_enum in self.app.review_btn_enums:
            self.update_review_info()
        elif btn_enum in self.app.run_btn_enums:
            loading_modal = LoadingModal()
            loading_modal.btn_enum = btn_enum
            self.app.push_screen(
                loading_modal,
                callback=self._process_loading_modal_result,
                wait_for_dismiss=True,
            )
        elif btn_enum == OpBtnEnum.refresh_tree:
            self._handle_reload_button()
            self.btn_enum = None
