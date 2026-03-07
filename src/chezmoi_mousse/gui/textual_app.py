import copy
import dataclasses
from math import ceil
from typing import TYPE_CHECKING, ClassVar

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import Button, TabbedContent, Tabs

from chezmoi_mousse import (
    CMD,
    IDS,
    BindingAction,
    BindingDescription,
    CachedData,
    Chars,
    OpBtnLabel,
    ReadCmd,
    TabLabel,
)

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.actionables import FlatButtonsVertical, SwitchSlider, TabButtons
from .common.loggers import AppLog, CmdLog
from .common.operate_mode import OperateMode
from .common.screen_header import CustomHeader
from .common.switchers import TreeSwitcher
from .config_tab import ConfigTab
from .help_tab import HelpTab
from .init_screen import InitChezmoi
from .install_help import InstallHelpScreen
from .logs_tab import LogsTab
from .main_screen import MainScreen
from .re_add_tab import ReAddTab
from .splash_screen import SplashScreen

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse import CommandResult

__all__ = ["ChezmoiGUI"]

chezmoi_mousse_dark = Theme(
    name="chezmoi-mousse-dark",
    dark=True,
    accent="#F187FB",
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DCDCDC",
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    surface="#101010",  # see also textual/theme.py
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)

chezmoi_mousse_light = Theme(
    name="chezmoi-mousse-light",
    dark=False,
    background="#DEDEDE",
    foreground="#000000",
    primary="#0060AA",
    accent="#790084",
    surface="#B8B8B8",
)


class ChezmoiGUI(App[None]):

    BINDINGS: ClassVar = [
        Binding(
            "ctrl+q",
            action="quit",
            description="Quit",
            key_display="Ctrl-q",
            priority=True,
        ),
        Binding(
            key="escape",
            action=BindingAction.exit_screen,
            description=OpBtnLabel.cancel,
        ),
        Binding(
            key="M,m",
            action=BindingAction.toggle_maximized,
            description=BindingDescription.maximize,
        ),
        Binding(
            key="F,f",
            action=BindingAction.toggle_switch_slider_visibility,
            description=BindingDescription.hide_filters,
        ),
        Binding(
            key="D,d",
            action=BindingAction.toggle_dry_run,
            description=BindingDescription.toggle_dry_run,
        ),
    ]

    CSS_PATH = "gui.tcss"

    def __init__(
        self, *, chezmoi_found: bool, dev_mode: bool, pretend_init_needed: bool
    ) -> None:
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

        self.chezmoi_found: bool = chezmoi_found
        self.dev_mode: bool = dev_mode
        self.force_init_needed: bool = pretend_init_needed
        self.init_needed: bool = bool(self.force_init_needed)
        self.init_cmd_result: CommandResult | None = None

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self._run_splash_screen()

    @work
    async def log_cmd_result(self, command_result: "CommandResult") -> None:
        # self.screen contains the currently active screen
        if (
            command_result.is_dry_run
            and command_result.cmd_enum in ReadCmd.all_read_cmds()
        ):
            # Don't log read results if it's a dry-run
            return
        self.screen.query_exactly_one(AppLog).log_cmd_result(command_result)
        self.screen.query_exactly_one(CmdLog).log_cmd_result(command_result)

    @work
    async def refresh_cmd_results(self) -> None:
        # Used in case of changes outside of the app.
        if CMD.run_cmd.changes_enabled is False:
            CMD.run_cmd.changes_enabled = True
        for read_cmd in (
            ReadCmd.managed,
            ReadCmd.status,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            cmd_result = CMD.run_cmd.read(read_cmd)
            setattr(CMD.cmd_results, f"{read_cmd.name}", cmd_result)
            cmd_logger = self.log_cmd_result(cmd_result)
            await cmd_logger.wait()
        CMD.run_cmd.changes_enabled = False
        old_cached = copy.deepcopy(CMD.cache)
        changed_paths = await self.get_changed_paths(old_cached).wait()
        if changed_paths:
            self.notify(f"Changed paths:\n{sorted(changed_paths)}")
        else:
            self.notify("No changes detected.", severity="warning")
        CMD.update_parsed_data()

    @work
    async def get_changed_paths(self, old_cached: CachedData) -> set["Path"]:
        old_managed = set(old_cached.managed_paths)
        old_files = set(old_cached.managed_file_paths)
        old_status = dict(old_cached.status_pairs)

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + Status changes
        changes = (old_managed ^ set(CMD.cache.managed_paths)) | {
            p
            for p in old_managed & set(CMD.cache.managed_paths)
            if old_status.get(p) != CMD.cache.status_pairs.get(p)
        }
        # Parent files to their directories
        all_files = old_files | set(CMD.cache.managed_file_paths)
        dirs = {p.parent if p in all_files else p for p in changes}

        # Reduce to common parents
        simplified: set[Path] = set()
        for path in sorted(dirs, key=lambda p: len(p.parts)):
            if not any(path.is_relative_to(parent) for parent in simplified):
                simplified.add(path)
        return simplified

    @work
    async def _run_splash_screen(self) -> None:
        if self.chezmoi_found is False:
            await self.push_screen(SplashScreen(), wait_for_dismiss=True)
            # Chezmoi command not found, SplashScreen will return None
            self.push_screen(InstallHelpScreen())
        elif self.init_needed is True:
            await self.push_screen(InitChezmoi(), wait_for_dismiss=True)
            await self.push_screen(SplashScreen(), wait_for_dismiss=True)
            self.push_screen(MainScreen())
        else:
            await self.push_screen(SplashScreen(), wait_for_dismiss=True)
            self.push_screen(MainScreen())

    ######################################################################
    # Helper methods for message handling and toggling widget visibility #
    ######################################################################

    def get_tab_widget(
        self,
    ) -> ApplyTab | ReAddTab | AddTab | LogsTab | ConfigTab | HelpTab:
        if not isinstance(self.screen, MainScreen):
            raise ValueError("get_tab_widget called outside of MainScreen")
        tab_to_query = self.screen.query_exactly_one(TabbedContent).active
        if tab_to_query == TabLabel.apply:
            return self.screen.query_exactly_one(ApplyTab)
        elif tab_to_query == TabLabel.re_add:
            return self.screen.query_exactly_one(ReAddTab)
        elif tab_to_query == TabLabel.add:
            return self.screen.query_exactly_one(AddTab)
        elif tab_to_query == TabLabel.config:
            return self.screen.query_exactly_one(ConfigTab)
        elif tab_to_query == TabLabel.help:
            return self.screen.query_exactly_one(HelpTab)
        elif tab_to_query == TabLabel.logs:
            return self.screen.query_exactly_one(LogsTab)
        else:
            raise ValueError(f"Unknown active_tab on MainScreen: {tab_to_query}")

    def get_switch_slider_widget(self) -> SwitchSlider:
        if not isinstance(self.screen, MainScreen):
            raise ValueError("get_switch_slider_widget called outside of MainScreen")
        tab_to_determine_id = self.screen.query_exactly_one(TabbedContent).active
        if tab_to_determine_id == TabLabel.apply:
            return self.screen.query_one(
                IDS.apply.container.switch_slider_q, SwitchSlider
            )
        elif tab_to_determine_id == TabLabel.re_add:
            return self.screen.query_one(
                IDS.re_add.container.switch_slider_q, SwitchSlider
            )
        else:  # tab_to_determine_id == TabLabel.add
            return self.screen.query_one(
                IDS.add.container.switch_slider_q, SwitchSlider
            )

    @on(Button.Pressed)
    def handle_exit_app_button(self, event: Button.Pressed) -> None:
        if event.button.label == OpBtnLabel.exit_app:
            self.exit()
            return

    ##################
    # Action Methods #
    ##################

    @on(TabbedContent.TabActivated)
    def tab_update_switch_slider_binding(
        self, event: TabbedContent.TabActivated
    ) -> None:
        if event.tabbed_content.active in (
            TabLabel.apply,
            TabLabel.re_add,
            TabLabel.add,
        ):
            slider: SwitchSlider = self.get_switch_slider_widget()
            slider_visible = slider.has_class("-visible")
            new_description = (
                BindingDescription.hide_filters
                if slider_visible is True
                else BindingDescription.show_filters
            )
            self.update_binding_description(
                binding_action=BindingAction.toggle_switch_slider_visibility,
                new_description=new_description,
            )
        self.refresh_bindings()

    def update_binding_description(
        self, binding_action: BindingAction, new_description: str
    ) -> None:
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
        CMD.run_cmd.changes_enabled = not CMD.run_cmd.changes_enabled
        self.screen.query_exactly_one(CustomHeader).changes_enabled = (
            CMD.run_cmd.changes_enabled
        )
        operate_mode_widgets = self.screen.query(OperateMode)
        for widget in operate_mode_widgets:
            if widget.display is True:
                widget.update_review_info()

    def action_toggle_switch_slider_visibility(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        slider: SwitchSlider = self.get_switch_slider_widget()
        slider_visible = slider.has_class("-visible")
        new_description = (
            BindingDescription.hide_filters
            if slider_visible is False
            else BindingDescription.show_filters
        )
        self.update_binding_description(
            binding_action=BindingAction.toggle_switch_slider_visibility,
            new_description=new_description,
        )
        slider.toggle_class("-visible")

    def action_toggle_maximized(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        active_tab = self.screen.query_exactly_one(TabbedContent).active
        left_side = None
        operation_buttons = None
        switch_slider = None
        view_switcher_buttons = None

        header = self.screen.query_exactly_one(CustomHeader)
        header.display = not header.display
        main_tabs = self.screen.query_exactly_one(Tabs)
        main_tabs.display = not main_tabs.display

        if active_tab in (TabLabel.apply, TabLabel.re_add):
            active_tab_widget = self.get_tab_widget()
            view_switcher_buttons = active_tab_widget.query(TabButtons).last()

        if active_tab == TabLabel.apply:
            left_side = self.screen.query_one(
                IDS.apply.container.left_side_q, TreeSwitcher
            )
            operation_buttons = self.screen.query_one(
                IDS.apply.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.apply.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabLabel.re_add:
            left_side = self.screen.query_one(
                IDS.re_add.container.left_side_q, TreeSwitcher
            )
            operation_buttons = self.screen.query_one(
                IDS.re_add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.re_add.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabLabel.add:
            left_side = self.screen.query_one(IDS.add.container.left_side_q, Vertical)
            operation_buttons = self.screen.query_one(
                IDS.add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.add.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabLabel.logs:
            logs_tab_buttons = self.screen.query(TabButtons).last()
            logs_tab_buttons.display = logs_tab_buttons.display is not True
        elif active_tab == TabLabel.config:
            left_side = self.screen.query_one(
                IDS.config.container.left_side_q, FlatButtonsVertical
            )
        elif active_tab == TabLabel.help:
            left_side = self.screen.query_one(
                IDS.help.container.left_side_q, FlatButtonsVertical
            )

        if left_side is not None:
            left_side.display = not left_side.display
        if operation_buttons is not None:
            operation_buttons.display = not operation_buttons.display
        if view_switcher_buttons is not None:
            view_switcher_buttons.display = not view_switcher_buttons.display
        if switch_slider is not None:
            switch_slider.display = not switch_slider.display

        new_description = (
            BindingDescription.maximize
            if header.display is True
            else BindingDescription.minimize
        )
        self.update_binding_description(
            binding_action=BindingAction.toggle_maximized,
            new_description=new_description,
        )

    def action_exit_screen(self) -> None:
        self.screen.dismiss()

    def check_action(
        self, action: str, parameters: tuple[object, ...]  # noqa: ARG002
    ) -> bool | None:
        if action == BindingAction.toggle_switch_slider_visibility:
            if isinstance(self.screen, MainScreen):
                header = self.screen.query_exactly_one(CustomHeader)
                switch_slider = self.get_switch_slider_widget()
                if header.display is False or switch_slider.display is False:
                    return False
                active_tab = self.screen.query_exactly_one(TabbedContent).active
                return active_tab in (TabLabel.apply, TabLabel.re_add, TabLabel.add)
            return False

        if action == BindingAction.toggle_dry_run:
            return isinstance(self.screen, (MainScreen, InitChezmoi))

        if action == BindingAction.toggle_maximized:
            if any(w.display for w in self.screen.query(OperateMode)):
                return False
            if isinstance(self.screen, (InstallHelpScreen, InitChezmoi)):
                return False

        if action == BindingAction.exit_screen:
            return not isinstance(self.screen, (InstallHelpScreen, MainScreen))

        return True


####################################################################################
# For monkey patching the textual ScrollBar.renderer method in ChezmoiGUI __init__ #
####################################################################################


class CustomScrollBarRender(ScrollBarRender):  # noqa: N806

    @classmethod
    def render_bar(
        cls,
        size: int = 25,
        virtual_size: float = 50,
        window_size: float = 20,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        back_color: Color | None = None,
        bar_color: Color | None = None,
    ) -> Segments:
        if back_color is None:
            back_color = Color.parse("#555555")
        if bar_color is None:
            bar_color = Color.parse("bright_magenta")

        bars = cls.VERTICAL_BARS if vertical else cls.HORIZONTAL_BARS

        back = back_color
        bar = bar_color

        len_bars = len(bars)
        width_thickness = thickness if vertical else 1

        _Segment = Segment  # noqa: N806
        _Style = Style  # noqa: N806
        blank = cls.BLANK_GLYPH * width_thickness

        foreground_meta = {"@mouse.down": "grab"}
        if window_size and size and virtual_size and size != virtual_size:
            bar_ratio = virtual_size / size
            thumb_size = max(1, window_size / bar_ratio)

            position_ratio = position / (virtual_size - window_size)
            position = (size - thumb_size) * position_ratio

            start = int(position * len_bars)
            end = start + ceil(thumb_size * len_bars)

            start_index, start_bar = divmod(max(0, start), len_bars)
            end_index, end_bar = divmod(max(0, end), len_bars)

            upper = {"@mouse.up": "scroll_up"}
            lower = {"@mouse.up": "scroll_down"}

            upper_back_segment = Segment(blank, _Style(bgcolor=back, meta=upper))
            lower_back_segment = Segment(blank, _Style(bgcolor=back, meta=lower))

            segments = [upper_back_segment] * int(size)
            segments[end_index:] = [lower_back_segment] * (size - end_index)
            if vertical:
                segments[start_index:end_index] = [
                    _Segment(
                        blank, _Style(color=bar, reverse=True, meta=foreground_meta)
                    )
                ] * (end_index - start_index)
                if start_index < len(segments):
                    bar_character = bars[len_bars - 1 - start_bar]
                    if bar_character != " ":
                        segments[start_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(bgcolor=back, color=bar, meta=foreground_meta)
                                if vertical
                                else _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                    reverse=True,
                                )
                            ),
                        )
                if end_index < len(segments):
                    bar_character = bars[len_bars - 1 - end_bar]
                    if bar_character != " ":
                        segments[end_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                    reverse=True,
                                )
                                if vertical
                                else _Style(
                                    bgcolor=back, color=bar, meta=foreground_meta
                                )
                            ),
                        )
            else:
                segments = [
                    _Segment(blank * width_thickness, _Style(bgcolor=back))
                ] * int(size)
                for i in range(start_index, end_index):
                    segments[i] = _Segment(
                        Chars.lower_3_8ths_block * width_thickness,
                        _Style(bgcolor=back, color=bar, meta=foreground_meta),
                    )
        else:
            style = _Style(bgcolor=back)
            segments = [_Segment(blank, style=style)] * int(size)
        if vertical:
            return Segments(segments, new_lines=True)
        else:
            return Segments((segments + [_Segment.line()]) * thickness, new_lines=False)
