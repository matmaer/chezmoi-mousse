from __future__ import annotations

import dataclasses
import json
from functools import partial
from typing import TYPE_CHECKING, ClassVar

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.widgets import Footer, Header, Static, TabbedContent, Tabs

from chezmoi_mousse import store
from chezmoi_mousse.debug.debug_tab import DebugTab
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.gui.common.actionables import (
    DryRunBtn,
    SwitchSlider,
)
from chezmoi_mousse.gui.common.contents import ContentsView
from chezmoi_mousse.gui.common.diffs import DiffView
from chezmoi_mousse.gui.common.doctor_data import DoctorTable
from chezmoi_mousse.gui.common.filtered_dir_tree import FilteredDirTree
from chezmoi_mousse.gui.common.git_log import GitLogView
from chezmoi_mousse.gui.common.loggers import AppLog, CmdLog
from chezmoi_mousse.gui.common.managed_tree import DestDirTree, ManagedTree
from chezmoi_mousse.gui.common.messages import CurrentNodeMsg
from chezmoi_mousse.gui.common.operate_modal import OperateModal
from chezmoi_mousse.gui.common.switchers import ViewSwitcher
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.str_enums import (
    BindingAction,
    BindingDescription,
    BtnLabel,
    Chars,
    ReactiveVar,
    ReadCmd,
    Tcss,
)
from chezmoi_mousse.theme import chezmoi_mousse_dark, chezmoi_mousse_light

from .common.actionables import FlatButtonsVertical, TabButtons
from .tab_panes import AddTab, ApplyTab, ConfigTab, LogsTab, ReAddTab

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.worker import Worker

    from chezmoi_mousse.named_tuples import CommandResult


__all__ = ["ChezmoiGui"]


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


class ChezmoiGui(App[str]):
    class MainVertical(Vertical): ...

    BINDINGS: ClassVar = [
        Binding(
            "ctrl+q",
            action="quit",
            description="Quit",
            key_display="Ctrl-q",
            priority=True,
        ),
        Binding(
            key="M,m",
            action=BindingAction.toggle_maximized,
            description=BindingDescription.maximize,
        ),
        Binding(
            key="F,f",
            action=BindingAction.toggle_switch_slider,
            description=BindingDescription.hide_filters,
        ),
        Binding(
            key="D,d",
            action=BindingAction.toggle_dry_run,
            description=BindingDescription.enable_live_run,
        ),
    ]

    CSS_PATH = "gui.tcss"

    def __init__(self) -> None:
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

    def _handle_exception(self, error: Exception) -> None:
        from chezmoi_mousse.debug.utils import DebugUtils

        DebugUtils.save_stacktrace()
        super()._handle_exception(error)

    def compose(self) -> ComposeResult:
        yield CustomHeader()
        yield TabbedContent()
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.splash_screen = SplashScreen()
        self.register_theme(chezmoi_mousse_light)
        self.run_startup_worker()

    @work
    async def run_startup_worker(self) -> None:
        await self.push_screen(self.splash_screen)
        await self.splash_screen.run_all_tasks()
        tabbed_content = self.query_exactly_one(TabbedContent)
        await tabbed_content.add_pane(ApplyTab())
        await tabbed_content.add_pane(ReAddTab())
        await tabbed_content.add_pane(AddTab())
        await tabbed_content.add_pane(LogsTab())
        await tabbed_content.add_pane(ConfigTab())
        if store.SHOW_DEBUG_TAB:
            await tabbed_content.add_pane(DebugTab())

        await tabbed_content.wait_for_refresh()
        await self._update_managed_trees().wait()
        await self.splash_screen.dismiss_after_fade_loop()

    # #####################
    # # UI update workers #
    # #####################

    def _listen_to_command_results(self, result: CommandResult) -> None:
        if result.cmd_enum is ReadCmd.doctor:
            doctor_table = self.query_exactly_one(DoctorTable)
            setattr(doctor_table, ReactiveVar.cmd_result, result)
        if result.cmd_enum is ReadCmd.cat_config:
            cat_config = self.query_exactly_one(ConfigTab.CatConfigStatic)
            cat_config.update(result.out_txt)
        if result.cmd_enum is ReadCmd.ignored:
            pretty_ignored = self.query_exactly_one(ConfigTab.PrettyIgnored)
            pretty_ignored.update(result.out_txt)
        if result.cmd_enum is ReadCmd.template_data:
            try:
                parsed_data = json.loads(result.std_out)
            except Exception as e:
                parsed_data = {"Cannot parse JSON": f"{e}"}
            pretty_template_data = self.query_exactly_one(ConfigTab.PrettyTemplateData)
            pretty_template_data.update(parsed_data)
        app_log = self.query_one(store.logs_ids.richlog.app_q, AppLog)
        setattr(app_log, ReactiveVar.cmd_result, result)
        cmd_log = self.query_one(store.logs_ids.container.cmd_log_q, CmdLog)
        setattr(cmd_log, ReactiveVar.cmd_result, result)

    @work
    async def _update_managed_trees(self) -> None:
        apply_managed_tree = self.query_one(store.apply_ids.managed_tree_q, ManagedTree)
        apply_managed_tree.update_tree()
        apply_managed_tree.refresh()
        re_add_managed_tree = self.query_one(
            store.re_add_ids.managed_tree_q, ManagedTree
        )
        re_add_managed_tree.update_tree()
        re_add_managed_tree.refresh()

    @work
    async def _reload_directory_tree_loading(self) -> None:
        # Update FilteredDirTree
        dir_tree = self.query_exactly_one(FilteredDirTree)
        dir_tree.reload()
        dir_tree.refresh()

    def run_chezmoi_command(self, command: ReadCmd) -> Worker[CommandResult]:
        return self.run_worker(
            partial(Commands.run_read_cmd, command, path_arg=None),
            thread=True,
            group="chezmoi_commands",
            name=command.name,
        )

    ####################
    # Message Handling #
    ####################

    @on(CurrentNodeMsg)
    def handle_new_tree_node_selected(self, msg: CurrentNodeMsg) -> None:
        if isinstance(self.screen, SplashScreen):
            return
        msg.stop()
        # Keep track of selected paths for each tab
        if msg.app_ids.tab_label == BtnLabel.add:
            store.add_path = msg.path
        elif msg.app_ids.tab_label == BtnLabel.apply:
            store.apply_path = msg.path
        elif msg.app_ids.tab_label == BtnLabel.re_add:
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
        self.query_one(msg.app_ids.container.git_log_q, GitLogView).node_msg = msg

    @on(TabbedContent.TabActivated)
    def tab_update_switch_slider_binding(
        self, event: TabbedContent.TabActivated
    ) -> None:
        active_pane = event.tabbed_content.active_pane
        if isinstance(active_pane, (AddTab, ApplyTab, ReAddTab)):
            slider = active_pane.query_exactly_one(SwitchSlider)
            slider_visible = slider.has_class("-visible")
            new_description = (
                BindingDescription.hide_filters
                if slider_visible is True
                else BindingDescription.show_filters
            )
            self._update_binding_description(
                binding_action=BindingAction.toggle_switch_slider,
                new_description=new_description,
            )
            self.refresh_bindings()

    # ##################
    # # Action Methods #
    # ##################

    def _update_binding_description(
        self, binding_action: BindingAction, new_description: str
    ) -> None:
        if isinstance(self.screen, SplashScreen):
            return
        for key, binding in self._bindings:
            if binding.action == binding_action:
                updated_binding = dataclasses.replace(
                    binding, description=new_description
                )
                if key in self._bindings.key_to_bindings:
                    bindings_list = self._bindings.key_to_bindings[key]
                    for i, b in enumerate(bindings_list):
                        if b.action == binding_action:
                            bindings_list[i] = updated_binding
                            break
                break
        self.refresh_bindings()

    def action_toggle_dry_run(self) -> None:
        if isinstance(self.screen, SplashScreen):
            return
        store.live_run = not store.live_run
        new_description = (
            BindingDescription.switch_to_dry_run
            if store.live_run is True
            else BindingDescription.enable_live_run
        )
        self._update_binding_description(
            binding_action=BindingAction.toggle_dry_run,
            new_description=new_description,
        )
        self.screen.query_exactly_one(CustomHeader).live_run = store.live_run
        if isinstance(self.screen, (OperateModal)):
            dry_run_btn = self.screen.query_exactly_one(DryRunBtn)
            dry_run_btn.label = (
                BtnLabel.enable_live_run
                if store.live_run is False
                else BtnLabel.switch_to_dry_run
            )

    def action_toggle_switch_slider(self) -> None:
        if isinstance(self.screen, SplashScreen):
            return
        slider = None
        tab_pane = self.query_exactly_one(TabbedContent).active_pane
        if not isinstance(tab_pane, (ApplyTab, ReAddTab, AddTab)):
            return
        slider = tab_pane.query_exactly_one(SwitchSlider)
        slider_visible = slider.has_class("-visible")
        new_description = (
            BindingDescription.hide_filters
            if slider_visible is False
            else BindingDescription.show_filters
        )
        self._update_binding_description(
            binding_action=BindingAction.toggle_switch_slider,
            new_description=new_description,
        )
        slider.toggle_class("-visible")

    def action_toggle_maximized(self) -> None:
        if isinstance(self.screen, SplashScreen):
            return
        active_tab_label = self.query_exactly_one(TabbedContent).active
        left_side: DestDirTree | Vertical | FlatButtonsVertical | None = None
        operation_buttons = None
        view_switcher_buttons = None

        header = self.query_exactly_one(CustomHeader)
        header.display = not header.display
        main_tabs = self.query_exactly_one(Tabs)
        main_tabs.display = not main_tabs.display

        if active_tab_label in (BtnLabel.apply, BtnLabel.re_add):
            tab_pane = self.query_exactly_one(TabbedContent).active_pane
            if tab_pane is None:
                return
            view_switcher_buttons = tab_pane.query(TabButtons).last()

        if active_tab_label == BtnLabel.apply:
            left_side = self.query_one(
                store.apply_ids.container.left_side_q, DestDirTree
            )
            operation_buttons = self.query_one(
                store.apply_ids.container.operate_buttons_q
            )
        elif active_tab_label == BtnLabel.re_add:
            left_side = self.query_one(
                store.re_add_ids.container.left_side_q, DestDirTree
            )
            operation_buttons = self.query_one(
                store.re_add_ids.container.operate_buttons_q
            )
        elif active_tab_label == BtnLabel.add:
            left_side = self.query_one(store.add_ids.container.left_side_q, Vertical)
            operation_buttons = self.query_one(
                store.add_ids.container.operate_buttons_q
            )
        elif active_tab_label == BtnLabel.logs:
            logs_tab_buttons = self.query(TabButtons).last()
            logs_tab_buttons.display = logs_tab_buttons.display is not True
        elif active_tab_label == BtnLabel.config:
            left_side = self.query_one(
                store.config_ids.container.left_side_q, FlatButtonsVertical
            )
        elif active_tab_label == BtnLabel.debug:
            left_side = self.query_one(
                store.debug_ids.container.left_side_q, FlatButtonsVertical
            )

        if left_side is not None:
            left_side.display = not left_side.display
        if operation_buttons is not None:
            operation_buttons.display = not operation_buttons.display
        if view_switcher_buttons is not None:
            view_switcher_buttons.display = not view_switcher_buttons.display

        tab_pane = self.query_exactly_one(TabbedContent).active_pane
        if tab_pane is None:
            return
        switch_slider = tab_pane.query_exactly_one(SwitchSlider)
        switch_slider.display = not switch_slider.display

        new_description = (
            BindingDescription.maximize
            if header.display is True
            else BindingDescription.minimize
        )
        self._update_binding_description(
            binding_action=BindingAction.toggle_maximized,
            new_description=new_description,
        )

    def check_action(
        self,
        action: str,
        parameters: tuple[object, ...],  # noqa: ARG002
    ) -> bool:
        if isinstance(self.screen, SplashScreen):
            return False
        active_pane = self.query_exactly_one(TabbedContent).active_pane
        if action == BindingAction.toggle_switch_slider:
            return isinstance(active_pane, (AddTab, ApplyTab, ReAddTab))
        if action == BindingAction.toggle_maximized:
            return isinstance(
                active_pane,
                (AddTab, ApplyTab, ReAddTab, ConfigTab, LogsTab, DebugTab),
            )
        return True


####################################################################################
# For monkey patching the textual ScrollBar.renderer method in ChezmoiGui __init__ #
####################################################################################


class CustomScrollBarRender(ScrollBarRender):
    HORIZONTAL_BARS: ClassVar[list[str]] = [Chars.lower_3_8ths_block] * 7 + [" "]

    @classmethod
    def render_bar(
        cls,
        size: int = 25,
        virtual_size: float = 50,
        window_size: float = 20,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        back_color: Color = Color.parse("#555555"),  # noqa: B008
        bar_color: Color = Color.parse("bright_magenta"),  # noqa: B008
    ) -> Segments:
        segments_object = super().render_bar(
            size,
            virtual_size,
            window_size,
            position,
            thickness,
            vertical,
            back_color,
            bar_color,
        )

        if vertical:  # For a vertical, render with the original render_bar
            return segments_object

        segments = list(segments_object.segments)

        for i, segment in enumerate(segments):
            if segment.style and segment.style.reverse:
                new_style = segment.style + Style(reverse=False)
                segments[i] = Segment(Chars.lower_3_8ths_block, new_style)

        return Segments(segments, new_lines=False)
