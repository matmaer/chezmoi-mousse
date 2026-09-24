from __future__ import annotations

import dataclasses
import os
import shutil
import sys
from typing import TYPE_CHECKING, ClassVar

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.widgets import Footer, Header, RadioButton, TabbedContent, Tabs
from textual.widgets._header import HeaderTitle

from chezmoi_mousse import store, tchezmoi
from chezmoi_mousse.debug.debug_tab import DebugLog, DebugTab
from chezmoi_mousse.gui.common.actionables import (
    FlatButtonsVertical,
    TabButtons,
)
from chezmoi_mousse.gui.common.loggers import AppLog, CmdLog
from chezmoi_mousse.gui.common.messages import CommandResultMsg
from chezmoi_mousse.gui.config_tab import ConfigTab
from chezmoi_mousse.gui.logs_tab import LogsTab
from chezmoi_mousse.gui.operate_tab import OperateTab
from chezmoi_mousse.gui.splash_screen import SplashScreen
from chezmoi_mousse.named_tuples import InitData
from chezmoi_mousse.str_enums import (
    BindingAction,
    BindingDescription,
    BtnLabel,
    Chars,
    LogStr,
    ReactiveVar,
    ReadCmd,
    Tcss,
    WriteCmd,
)
from chezmoi_mousse.theme import chezmoi_mousse_dark, chezmoi_mousse_light

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from chezmoi_mousse.named_tuples import CommandResult


__all__ = ["ChezmoiGui"]


RadioButton.BUTTON_INNER = Chars.radio_button


class CustomHeader(Header):
    DRY_MODE: ClassVar[str] = (
        "-  c h e z m o i  m o u s s e  --  d r y  r u n  m o d e  -"
    )
    LIVE_MODE: ClassVar[str] = "-  c h e z m o i  m o u s s e  --  l i v e  m o d e  -"

    live_run: reactive[bool] = reactive(False)

    def on_mount(self) -> None:
        self.icon = Chars.burger

    def watch_live_run(self, live_run: bool) -> None:
        header_title = self.query_exactly_one(HeaderTitle)
        if live_run is True:
            self.screen.title = self.LIVE_MODE
            header_title.add_class(Tcss.live_run_color)
        elif live_run is False:
            self.screen.title = self.DRY_MODE
            header_title.remove_class(Tcss.live_run_color)


class ChezmoiGui(App[str]):
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

        store.init_data = InitData(
            which_chezmoi=shutil.which("chezmoi"),
            which_git=shutil.which("git"),
            pilot_mode=(
                os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
                or "--pilot-mode" in sys.argv
            ),
        )
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
        self.splash_screen = SplashScreen(name="splash_screen")
        self.register_theme(chezmoi_mousse_light)
        self._run_startup_worker()

    @work
    async def _run_startup_worker(self) -> None:
        await self.push_screen(self.splash_screen)

        self.init_phase = True
        results: list[CommandResult] = []
        for cmd in (ReadCmd.git_dir, WriteCmd.init, ReadCmd.dump_config):
            cmd_result = await tchezmoi.run_chezmoi_cmd(self, cmd)
            results.append(cmd_result)
        await store.decode_and_store_config(results[-1].std_out)
        await self.splash_screen.write_log_msg(
            prefix_suffix=(ReadCmd.dump_config.pretty_cmd, LogStr.decoded)
        )

        tabbed_content = self.query_exactly_one(TabbedContent)

        await tabbed_content.add_pane(LogsTab())
        await tabbed_content.add_pane(ConfigTab())
        await tabbed_content.add_pane(DebugTab())

        self.app_log = self.query_one(store.logs_ids.richlog.app_q, AppLog)
        self.cmd_log = self.query_one(store.logs_ids.container.cmd_log_q, CmdLog)
        self.debug_log = self.query_one(store.debug_ids.richlog.debug_q, DebugLog)
        self.init_phase = False
        for cr in results:
            setattr(self.cmd_log, ReactiveVar.cmd_result, cr)
            setattr(self.app_log, ReactiveVar.cmd_result, cr)
        self._run_splash_commands()

        await tchezmoi.run_managed_commands(self)
        await tabbed_content.add_pane(OperateTab(), before=BtnLabel.logs.pane_id)
        tabbed_content.active = BtnLabel.operate.pane_id
        await self.splash_screen.dismiss_after_fade_loop()

    @work
    async def _run_splash_commands(self) -> None:
        await tchezmoi.run_in_task_group(
            self,
            (
                ReadCmd.doctor,
                ReadCmd.cat_config,
                ReadCmd.git_remote,
                ReadCmd.ignored,
                ReadCmd.template_data,
            ),
        )

    @on(CommandResultMsg)
    def handle_command_result(self, msg: CommandResultMsg) -> None:
        if msg.cmd_result.cmd_enum in (
            ReadCmd.doctor,
            ReadCmd.cat_config,
            ReadCmd.ignored,
            ReadCmd.template_data,
        ):
            config_tab = self.query_exactly_one(ConfigTab)
            # the reactives trigger each update in a worker
            setattr(config_tab, ReactiveVar.cmd_result, msg.cmd_result)

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
        custom_header = self.screen.query_exactly_one(CustomHeader)
        custom_header.live_run = store.live_run

    def action_toggle_maximized(self) -> None:
        if isinstance(self.screen, SplashScreen):
            return
        active_tab_label = self.query_exactly_one(TabbedContent).active
        left_side: FlatButtonsVertical | None = None
        operation_buttons = None
        view_switcher_buttons = None

        header = self.query_exactly_one(CustomHeader)
        header.display = not header.display
        main_tabs = self.query_exactly_one(Tabs)
        main_tabs.display = not main_tabs.display

        if active_tab_label == BtnLabel.logs:
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
        parameters: tuple[object, ...],
    ) -> bool:
        _ = parameters
        if isinstance(self.screen, SplashScreen):
            return False
        if action == BindingAction.toggle_maximized:
            active_pane = self.query_exactly_one(TabbedContent).active_pane
            return isinstance(
                active_pane,
                (OperateTab, ConfigTab, LogsTab, DebugTab),
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
