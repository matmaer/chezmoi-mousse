from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, TabbedContent, TabPane, Tabs

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    FlatBtnLabel,
    LogString,
    OpBtnEnum,
    OpBtnLabel,
    TabLabel,
)

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.actionables import TabButtons
from .common.loggers import AppLog, DebugLog
from .common.messages import ChangedPathsMsg, OperateButtonMsg
from .common.operate_mode import OperateMode
from .common.screen_header import CustomHeader
from .common.switchers import TreeSwitcher
from .common.trees import ListTree, ManagedTree
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .logs_tab import LogsTab
from .re_add_tab import ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["MainScreen"]


class MainScreen(Screen[None], AppType):

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield OperateMode(IDS.main_tabs)
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
        self.operate_mode_container = self.query_one(
            IDS.main_tabs.container.op_mode_q, OperateMode
        )
        self.app_log = self.query_one(IDS.logs.logger.app_q, AppLog)
        # Debug logger if in dev mode
        if self.app.dev_mode is True:
            self.debug_log = self.query_one(IDS.debug.logger.debug_q, DebugLog)
            self.app_log.success(LogString.dev_mode_enabled)
            self.notify(LogString.dev_mode_enabled)

        self._populate_apply_trees()
        self._populate_re_add_trees()
        self._set_config_screen_reactives()
        self.app.call_later(self._log_splash_log_commands)

    def _set_config_screen_reactives(self) -> None:
        config_tab = self.screen.query_exactly_one(ConfigTab)
        config_tab.command_results = CMD.cmd_results

    def _log_splash_log_commands(self) -> None:
        self.app_log.info("--- Commands executed in loading screen ---")
        commands_to_log = CMD.cmd_results.executed_commands
        for cmd in commands_to_log:
            self.app.log_cmd_result(cmd)
        self.app_log.info("--- End of loading screen commands ---")

    def _populate_apply_trees(self) -> None:
        self.screen.query_one(IDS.apply.tree.managed_q, ManagedTree).populate_tree()
        self.app_log.success("Apply tab managed tree populated.")
        self.screen.query_one(IDS.apply.tree.list_q, ListTree).populate_tree()
        self.app_log.success("Apply tab list tree populated.")

    @work
    async def _populate_re_add_trees(self) -> None:
        self.screen.query_one(IDS.re_add.tree.managed_q, ManagedTree).populate_tree()
        self.app_log.success("Re-Add tab managed tree populated.")
        self.screen.query_one(IDS.re_add.tree.list_q, ListTree).populate_tree()
        self.app_log.success("Re-Add tab list tree populated.")

    #######################
    # Operate mode helper #
    #######################

    def _toggle_operate_display(self, ids: "AppIds") -> None:
        main_tabs = self.screen.query_exactly_one(Tabs)
        main_tabs.display = not main_tabs.display
        if ids.canvas_name in (TabLabel.apply, TabLabel.re_add):
            left_side = self.screen.query_one(ids.container.left_side_q, TreeSwitcher)
            left_side.display = not left_side.display
            active_tab_widget = self.app.get_tab_widget()
            view_switcher_buttons = active_tab_widget.query(TabButtons).last()
            view_switcher_buttons.display = not view_switcher_buttons.display
        elif ids.canvas_name == TabLabel.add:
            left_side = self.screen.query_one(ids.container.left_side_q, Vertical)
            left_side.display = not left_side.display
        switch_slider = self.app.get_switch_slider_widget()
        switch_slider.display = not switch_slider.display

    ############################
    # Message handling methods #
    ############################

    @on(Button.Pressed)
    async def refresh_tree(self, event: Button.Pressed) -> None:
        if event.button.label == FlatBtnLabel.refresh_tree:
            event.stop()
            await self.operate_mode_container.manual_refresh().wait()
            apply_managed_tree = self.query_one(IDS.apply.tree.managed_q, ManagedTree)
            apply_managed_tree.populate_tree()
            apply_list_tree = self.query_one(IDS.apply.tree.list_q, ListTree)
            apply_list_tree.populate_tree()
            re_add_managed_tree = self.query_one(IDS.re_add.tree.managed_q, ManagedTree)
            re_add_managed_tree.populate_tree()
            re_add_list_tree = self.query_one(IDS.re_add.tree.list_q, ListTree)
            re_add_list_tree.populate_tree()

    @on(ChangedPathsMsg)
    def handle_changed_paths_msg(self, msg: ChangedPathsMsg) -> None:
        if not msg.changed_paths:
            self.notify("No managed paths changed.", severity="warning")
        else:
            changed_paths = "\n".join(sorted(str(path) for path in msg.changed_paths))
            self.notify(f"Changed paths:\n{changed_paths}")

    @on(OperateButtonMsg)
    def handle_operate_btn_msg(self, msg: OperateButtonMsg) -> None:
        operate_mode_container = self.screen.query_exactly_one(OperateMode)
        if msg.button.btn_enum in (OpBtnLabel.cancel, OpBtnLabel.reload):
            operate_mode_container.display = False
            self._toggle_operate_display(msg.ids)
        elif msg.button.btn_enum in OpBtnEnum.review_btn_enums():
            operate_mode_container.btn_enum = msg.button.btn_enum
            operate_mode_container.display = True
            self._toggle_operate_display(msg.ids)
        elif msg.button.btn_enum in OpBtnEnum.run_btn_enums():
            operate_mode_container.btn_enum = msg.button.btn_enum
