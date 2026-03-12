from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
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
from .common.actionables import SwitchSlider
from .common.contents import ContentsView
from .common.diffs import DiffView
from .common.filtered_dir_tree import FilteredDirTree
from .common.git_log import GitLogView
from .common.loading_modal import LoadingModal, LoadingModalResult, min_wait
from .common.loggers import AppLog, CmdLog
from .common.messages import LoadingResultMsg, LogCmdResultMsg, OperateButtonMsg
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

__all__ = ["MainScreen", "OperateMode"]


class OperateMode(Vertical, AppType):

    btn_enum: reactive[OpBtnEnum | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(id=IDS.main_tabs.container.op_mode)

    def compose(self) -> ComposeResult:
        yield Static(
            id=IDS.main_tabs.static.operate_info,
            classes=Tcss.operate_info,
            name="operate info",
        )
        yield ScrollableContainer(
            id=IDS.main_tabs.container.command_output, name="operate command results"
        )

    def on_mount(self) -> None:
        self.display = False
        self.operate_info = self.query_one(IDS.main_tabs.static.operate_info_q, Static)
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
        if btn_enum in self.review_btn_enums:
            self.update_review_info()
        elif btn_enum in self.run_btn_enums:
            loading_modal = LoadingModal()
            loading_modal.btn_enum = btn_enum
            self.app.push_screen(
                loading_modal,
                callback=self._process_loading_modal_result,
                wait_for_dismiss=True,
            )

    def _process_loading_modal_result(
        self, result: "LoadingModalResult | None"
    ) -> None:
        if result is None or self.btn_enum is None:
            return
        self.post_message(LoadingResultMsg(loading_result=result))
        log_collapsibles = self.query_one(
            IDS.main_tabs.container.command_output_q, ScrollableContainer
        )
        log_collapsibles.remove_children()
        log_collapsibles.mount(Label("Command output", classes=Tcss.main_section_label))
        if result.write_cmd_result is not None:
            log_collapsibles.mount(result.write_cmd_result.pretty_collapsible)
        for cmd_result in result.read_cmd_results:
            log_collapsibles.mount(cmd_result.pretty_collapsible)
        log_collapsibles.mount(Label("Changed paths", classes=Tcss.main_section_label))
        if not result.changed_paths:
            dry_run = (
                " (dry run)"
                if result.write_cmd_result and result.write_cmd_result.is_dry_run
                else ""
            )
            log_collapsibles.mount(Static(f"No paths changed.{dry_run}"))
        for path in result.changed_paths:
            log_collapsibles.mount(Static(str(path), classes=Tcss.info))

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
        if IDS.main_tabs.canvas_name in (TabLabel.add, TabLabel.re_add):
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        self.operate_info.update("\n".join(info_lines))
        self.operate_info.border_title = self.btn_enum.op_info_title
        self.operate_info.border_subtitle = self.btn_enum.op_info_subtitle

    @work
    async def manual_refresh(self) -> None:
        loading_modal = LoadingModal()
        await self.app.push_screen(loading_modal)
        await loading_modal.run_all_read_commands().wait()
        loading_modal.dismiss()


class MainScreen(Screen[None], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.last_loading_result: LoadingModalResult = LoadingModalResult()

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield OperateMode()
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
        self.operate_mode = self.query_one(
            IDS.main_tabs.container.op_mode_q, OperateMode
        )
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        # Debug logger if in dev mode
        if self.app.dev_mode is True:
            self.notify(LogString.dev_mode_enabled)
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self._populate_apply_trees()
        self._populate_re_add_trees()
        self._set_config_screen_reactives()
        self.app.call_later(self._log_splash_log_commands)

        self.contents_views = list(self.query(ContentsView))
        self.diff_views = list(self.query(DiffView))
        self.dir_tree = self.query_exactly_one(FilteredDirTree)
        self.git_logs = list(self.query(GitLogView))
        self.list_trees = list(self.query(ListTree))
        self.managed_trees = list(self.query(ManagedTree))

    def log_cmd_result(self, command_result: "CommandResult") -> None:
        app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        app_log.cmd_result = command_result
        cmd_log = self.query_one(IDS.logs.logger.cmd_q, CmdLog)
        cmd_log.cmd_result = command_result

    def _set_config_screen_reactives(self) -> None:
        config_tab = self.query_exactly_one(ConfigTab)
        config_tab.command_results = CMD.cmd_results

    def _log_splash_log_commands(self) -> None:
        self.app_log.write_ready("Commands executed in loading screen")
        commands_to_log = CMD.cmd_results.executed_commands
        for cmd in commands_to_log:
            self.log_cmd_result(cmd)
        self.app_log.write_ready("End of loading screen commands")

    def _populate_apply_trees(self) -> None:
        self.query_one(IDS.apply.tree.managed_q, ManagedTree).populate_tree()
        self.app_log.write_info("Apply tab managed tree populated.")
        self.query_one(IDS.apply.tree.list_q, ListTree).populate_tree()
        self.app_log.write_info("Apply tab list tree populated.")

    def _populate_re_add_trees(self) -> None:
        self.query_one(IDS.re_add.tree.managed_q, ManagedTree).populate_tree()
        self.app_log.write_info("Re-Add tab managed tree populated.")
        self.query_one(IDS.re_add.tree.list_q, ListTree).populate_tree()
        self.app_log.write_info("Re-Add tab list tree populated.")

    #######################
    # Operate mode helper #
    #######################

    def _set_review_display(self, ids: "AppIds") -> None:
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            left_side = self.query_one(ids.container.left_side_q, TreeSwitcher)
        elif ids.canvas_name == TabLabel.add:
            left_side = self.query_one(ids.container.left_side_q, Vertical)
        else:
            self.notify(f"Not yet implemented for {ids.canvas_name}", severity="error")
            return
        self.query_exactly_one(Tabs).display = False
        left_side.display = False
        switch_slider: SwitchSlider | None = self.app.get_switch_slider_widget()
        if switch_slider is not None:
            switch_slider.display = False

    def _set_post_run_display(self, ids: "AppIds") -> None:
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            right_side = self.query_one(ids.container.right_side_q, ViewSwitcher)
        elif ids.canvas_name == TabLabel.add:
            right_side = self.query_one(ids.container.contents_q, ContentsView)
        else:
            self.notify(f"Not yet implemented for {ids.canvas_name}", severity="error")
            return
        right_side.display = False

    def _restore_display(self, ids: "AppIds") -> None:
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            left_side = self.query_one(ids.container.left_side_q, TreeSwitcher)
            right_side = self.query_one(ids.container.right_side_q, ViewSwitcher)
        elif ids.canvas_name == TabLabel.add:
            left_side = self.query_one(ids.container.left_side_q, Vertical)
            right_side = self.query_one(ids.container.contents_q, ContentsView)
        else:
            self.notify(f"Not yet implemented for {ids.canvas_name}", severity="error")
            return
        self.query_exactly_one(Tabs).display = True
        left_side.display = True
        right_side.display = True
        switch_slider: SwitchSlider | None = self.app.get_switch_slider_widget()
        if switch_slider is not None:
            switch_slider.display = True

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

    ############################
    # Message handling methods #
    ############################

    @on(Button.Pressed)
    async def refresh_all_trees(self, event: Button.Pressed) -> None:
        if event.button.label == OpBtnLabel.refresh_tree:
            self.notify("not yet implemented refresh all trees")
            event.stop()
            await self.operate_mode.manual_refresh().wait()

    @work
    async def _handle_reload_button(self) -> None:
        loading_modal = LoadingModal()
        self.app.push_screen(loading_modal)
        label = loading_modal.query_exactly_one(Label)
        label.update("logging result to app and cmd log")
        await self._log_loading_cmd_results(
            self.last_loading_result.all_cmd_results
        ).wait()
        label.update("updating trees")
        await self._update_trees(self.last_loading_result.changed_paths).wait()

    @on(OperateButtonMsg)
    def handle_operate_btn_msg(self, msg: OperateButtonMsg) -> None:
        msg.stop()
        operate_mode = self.query_exactly_one(OperateMode)
        if msg.button.btn_enum in (OpBtnLabel.cancel, OpBtnLabel.reload):
            operate_mode.display = False
            self._restore_display(msg.ids)
        if msg.button.btn_enum == OpBtnLabel.reload:
            self._handle_reload_button()
            return
        if msg.button.btn_enum in OpBtnEnum.review_btn_enums():
            operate_mode.display = True
            operate_mode.btn_enum = msg.button.btn_enum
            self._set_review_display(msg.ids)
        elif msg.button.btn_enum in OpBtnEnum.run_btn_enums():
            operate_mode.btn_enum = msg.button.btn_enum
            self._set_post_run_display(msg.ids)

    @on(LogCmdResultMsg)
    def log_new_cmd_result(self, msg: LogCmdResultMsg) -> None:
        self.log_cmd_result(msg.cmd_result)

    @on(LoadingResultMsg)
    def handle_changed_root_paths(self, msg: LoadingResultMsg) -> None:
        self.last_loading_result = msg.loading_result
        self.notify(f"received LoadingResultMsg {msg}")
