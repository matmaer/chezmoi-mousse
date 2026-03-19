import json
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    Footer,
    Label,
    Static,
    TabbedContent,
    TabPane,
    Tabs,
)

from chezmoi_mousse import (
    CMD,
    IDS,
    AppType,
    CommandResult,
    LogString,
    OpBtnEnum,
    OpBtnLabel,
    OperateString,
    OpInfoString,
    ReadCmd,
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
from .common.loading_modal import LoadingLabel, LoadingModal, min_wait
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
        self.current_button: OpButton | None = None

    def on_mount(self) -> None:
        self.display = False

    def update_review_info(self, button: OpButton) -> None:
        self.current_button = button
        info_lines: list[str] = []
        path_arg = (
            str(button.btn_enum.path_arg)
            if button.btn_enum.path_arg is not None
            else ""
        )
        info_lines.append(
            CMD.run_cmd.review_cmd(
                global_args=(*button.btn_enum.write_cmd.value, path_arg)
            )
        )
        info_lines.append(button.btn_enum.op_info_string)
        if button.btn_enum != OpBtnEnum.apply_review:
            if CMD.cache.git_auto_commit is True:
                info_lines.append(OperateString.auto_commit)
            if CMD.cache.git_auto_push is True:
                info_lines.append(OperateString.auto_push)
        else:
            info_lines.append(
                "[dim]Apply operation: auto-commit and auto-push not applicable[/]"
            )
        self.update("\n".join(info_lines))
        self.border_title = button.btn_enum.op_info_title
        self.border_subtitle = button.btn_enum.op_info_subtitle

    @work
    async def update_write_cmd_info(self) -> None:
        self.update(
            f"{CMD.loading_modal_results[0].exit_code_colored_cmd}\n"
            f"Exit code {CMD.loading_modal_results[0].exit_code}"
        )
        self.border_title = OpInfoString.command_completed
        self.border_subtitle = None

    def watch_changes_enabled(self) -> None:
        if not self.display or self.current_button is None:
            return
        self.update_review_info(self.current_button)


class CommandOutput(ScrollableContainer):

    def __init__(self) -> None:
        super().__init__(id=IDS.main_tabs.container.command_output)

    def compose(self) -> ComposeResult:
        yield Label("Changed paths", classes=Tcss.main_section_label)
        yield Static(id=IDS.main_tabs.static.changed_paths, classes=Tcss.info)
        yield Label("Command output", classes=Tcss.main_section_label)

    def on_mount(self) -> None:
        self.changed_paths_static = self.query_one(
            IDS.main_tabs.static.changed_paths_q, Static
        )

    @work
    async def update_mounted(self) -> None:
        if not CMD.changed_paths:
            dry_run = (
                " (dry run)"
                if any(
                    cmd_result.is_dry_run for cmd_result in CMD.loading_modal_results
                )
                else ""
            )
            self.changed_paths_static.update(f"No paths changed.{dry_run}")
        else:
            changed_paths_strings = "\n".join(str(path) for path in CMD.changed_paths)
            self.changed_paths_static.update(changed_paths_strings)
        for cmd_result in CMD.loading_modal_results:
            self.mount(cmd_result.pretty_collapsible)


class OpFeedBack(Vertical):

    def __init__(self) -> None:
        super().__init__(id=IDS.main_tabs.container.op_feed_back)

    def compose(self) -> ComposeResult:
        yield OperateInfo()
        yield CommandOutput()

    def on_mount(self) -> None:
        self.display = False


class MainScreen(Screen[None], AppType):

    READ_CMDS: ClassVar[list[ReadCmd]] = [
        ReadCmd.managed_dirs,
        ReadCmd.managed_files,
        ReadCmd.status_dirs,
        ReadCmd.status_files,
    ]

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
            IDS.main_tabs.container.op_feed_back_q, OpFeedBack
        )
        self.operate_info = self.query_one(
            IDS.main_tabs.static.operate_info_q, OperateInfo
        )
        self.command_output = self.query_one(
            IDS.main_tabs.container.command_output_q, CommandOutput
        )
        self.command_output.display = False
        self._push_loading_modal(None)

    ###########################################
    # Push modal methods with their callbacks #
    ###########################################

    @work
    async def _push_loading_modal(self, btn_enum: OpBtnEnum | None) -> None:
        self.loading_modal = LoadingModal(btn_enum)
        await self.app.push_screen(self.loading_modal)

        if btn_enum is None and self.app.chezmoi_found is True:
            if CMD.cache.dump_config is not None:
                await self._update_parsed_config(CMD.cache.dump_config.std_out).wait()
            await self._update_trees().wait()
            cmd_results = [
                attr
                for attr in vars(CMD.cache).values()
                if isinstance(attr, CommandResult)
            ]
            await self._log_all_cmd_results(cmd_results).wait()
            await self._update_config_tab().wait()
            self.loading_modal.dismiss()
        elif btn_enum in self.app.run_btn_enums:
            await self.loading_modal.run_write_command(btn_enum).wait()
            await self.operate_info.update_write_cmd_info().wait()
            for read_cmd in self.READ_CMDS:
                await self.loading_modal.run_read_command(read_cmd).wait()
            await self.loading_modal.update_changed_paths().wait()
            await self.command_output.update_mounted().wait()
            self.loading_modal.dismiss()
        elif btn_enum == OpBtnEnum.refresh_tree:
            for read_cmd in self.READ_CMDS:
                await self.loading_modal.run_read_command(read_cmd).wait()
            await self.loading_modal.update_changed_paths().wait()
            await self.command_output.update_mounted().wait()
            self.loading_modal.dismiss()
        elif btn_enum == OpBtnEnum.reload:
            if len(CMD.changed_paths) == 0:
                self.notify(
                    "No changed managed paths found, skipping refresh.",
                    severity="warning",
                )
                self.loading_modal.dismiss()
            else:
                await self._purge_views_cache().wait()
                await self._update_trees().wait()
                await self._log_all_cmd_results(CMD.loading_modal_results).wait()
                self.loading_modal.dismiss()
        else:
            raise NotImplementedError(f"Button enum {btn_enum} not implemented")

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
        for view in chain(diff_views, contents_views, git_log_views):
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
    async def _update_parsed_config(self, dump_config: str) -> None:
        try:
            self.loading_modal.label_text = LoadingLabel.parse_dump_config.with_color
            parsed_cfg = json.loads(dump_config)
            CMD.cache.dest_dir = Path(parsed_cfg["destDir"])
            CMD.cache.git_auto_commit = parsed_cfg["git"]["autocommit"]
            CMD.cache.git_auto_push = parsed_cfg["git"]["autopush"]
        except Exception:
            pass

    @work
    @min_wait
    async def _update_trees(self) -> None:
        self.loading_modal.label_text = LoadingLabel.update_trees.with_color
        apply_list_tree = self.query_one(IDS.apply.tree.list_q, ListTree)
        apply_managed_tree = self.query_one(IDS.apply.tree.managed_q, ManagedTree)
        re_add_list_tree = self.query_one(IDS.re_add.tree.list_q, ListTree)
        re_add_managed_tree = self.query_one(IDS.re_add.tree.managed_q, ManagedTree)
        apply_list_tree.populate_tree()
        apply_managed_tree.populate_tree()
        re_add_list_tree.populate_tree()
        re_add_managed_tree.populate_tree()
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
        if event.button.btn_enum in self.app.review_btn_enums:
            self.operate_info.update_review_info(event.button)
            return
        if event.button.btn_enum == OpBtnEnum.reload:
            collapsibles = self.command_output.query(Collapsible).results()
            for collapsible in collapsibles:
                collapsible.remove()
            await self._push_loading_modal(OpBtnEnum.reload).wait()
        elif (
            event.button.btn_enum in self.app.run_btn_enums
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
            has_status = msg.path in CMD.cache.file_status_pairs
            self.query_one(ids.tab_operation_btn_q, Button).disabled = not has_status
            for btn_id_q in ids.forget_destroy_review_btn_qids:
                self.query_one(btn_id_q, Button).disabled = not has_status
        elif msg.path in CMD.cache.managed_dirs_with_dest_dir:
            if msg.path == CMD.cache.dest_dir:
                for btn_id_q in ids.forget_destroy_review_btn_qids:
                    self.query_one(btn_id_q, Button).disabled = True
                if CMD.cache.no_status_paths is True:
                    self.query_one(ids.tab_operation_btn_q, Button).disabled = True
            else:
                for btn_id_q in ids.forget_destroy_review_btn_qids:
                    self.query_one(btn_id_q, Button).disabled = False
                self.query_one(ids.tab_operation_btn_q, Button).disabled = bool(
                    msg.path not in CMD.cache.dir_status_pairs
                    and msg.path not in CMD.cache.x_dirs_with_status_children
                )

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
        cancel_btn = self.query_one(button.app_ids.op_btn.cancel_q, OpButton)
        reload_btn = self.query_one(button.app_ids.op_btn.reload_q, OpButton)
        run_buttons = [b for b in op_buttons if b.id in button.app_ids.run_btn_ids]
        review_buttons = [
            b for b in op_buttons if b.id in button.app_ids.review_btn_ids
        ]
        if button.id in (button.app_ids.op_btn.cancel, button.app_ids.op_btn.reload):
            cancel_btn.display = False
            reload_btn.display = False
            for btn in run_buttons:
                btn.display = False
            for btn in review_buttons:
                btn.display = True
        elif button in review_buttons:
            cancel_btn.display = True
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
        elif button in run_buttons:
            cancel_btn.display = False
            reload_btn.display = True
            button.disabled = True
        elif button.btn_enum == OpBtnEnum.refresh_tree:
            cancel_btn.display = False
            reload_btn.display = True
            for btn in review_buttons:
                btn.display = False
            for btn in run_buttons:
                btn.display = False

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
        self._get_set_button_display(button)
        if button.btn_enum in (OpBtnEnum.cancel, OpBtnEnum.reload):
            self._get_set_left_side_display(button.app_ids, True)
            self._get_set_right_side_display(button.app_ids, True)
            self._get_set_switch_slider_display(True)
            self.main_tabs.display = True
            self.op_feed_back.display = False
            self.command_output.display = False
            self.operate_info.display = False
            return
        self.op_feed_back.display = True
        self.main_tabs.display = False
        self._get_set_left_side_display(button.app_ids, False)
        self._get_set_switch_slider_display(False)
        if button.btn_enum in self.app.review_btn_enums:
            self.command_output.display = False
            self.operate_info.display = True
            self._get_set_right_side_display(button.app_ids, True)
        elif button.btn_enum in self.app.run_btn_enums:
            self.command_output.display = True
            self.operate_info.display = True
            self._get_set_right_side_display(button.app_ids, False)
        elif button.btn_enum == OpBtnEnum.refresh_tree:
            self.command_output.display = True
            self.operate_info.display = False
            self._get_set_right_side_display(button.app_ids, False)
