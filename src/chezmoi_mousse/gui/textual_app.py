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
    AppIds,
    BindingAction,
    BindingDescription,
    Chars,
    OpBtnEnum,
    OpBtnLabel,
    ReadCmd,
    TabName,
)

from .add_tab import AddTab
from .apply_tab import ApplyTab
from .common.actionables import FlatButtonsVertical, SwitchSlider, TabButtons
from .common.loggers import AppLog, CmdLog
from .common.messages import ChangedPathsMsg, OperateButtonMsg
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
            description=BindingDescription.cancel,
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

        self.changes_enabled = False
        self.chezmoi_found: bool = chezmoi_found
        self.dev_mode: bool = dev_mode
        self.force_init_needed: bool = pretend_init_needed
        self.init_needed: bool = True if self.force_init_needed else False
        self.init_cmd_result: CommandResult | None = None

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self._run_splash_screen()

    @work
    async def log_cmd_result(self, command_result: "CommandResult") -> None:
        # self.screen contains the currently active screen
        self.screen.query_exactly_one(AppLog).log_cmd_result(command_result)
        self.screen.query_exactly_one(CmdLog).log_cmd_result(command_result)

    @work
    async def refresh_cmd_results(self) -> None:
        for read_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            cmd_result = CMD.run_cmd.read(read_cmd)
            setattr(CMD.cmd_results, f"{read_cmd.name}", cmd_result)
            cmd_logger = self.log_cmd_result(cmd_result)
            await cmd_logger.wait()
        CMD.update_parsed_data()

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

    def _get_tab_widget(
        self,
    ) -> ApplyTab | ReAddTab | AddTab | LogsTab | ConfigTab | HelpTab:
        if not isinstance(self.screen, MainScreen):
            raise ValueError("get_tab_widget called outside of MainScreen")
        tab_to_query = self.screen.query_exactly_one(TabbedContent).active
        if tab_to_query == TabName.apply:
            return self.screen.query_exactly_one(ApplyTab)
        elif tab_to_query == TabName.re_add:
            return self.screen.query_exactly_one(ReAddTab)
        elif tab_to_query == TabName.add:
            return self.screen.query_exactly_one(AddTab)
        elif tab_to_query == TabName.config:
            return self.screen.query_exactly_one(ConfigTab)
        elif tab_to_query == TabName.help:
            return self.screen.query_exactly_one(HelpTab)
        elif tab_to_query == TabName.logs:
            return self.screen.query_exactly_one(LogsTab)
        else:
            raise ValueError(f"Unknown active_tab on MainScreen: {tab_to_query}")

    def _get_switch_slider_widget(self) -> SwitchSlider:
        if not isinstance(self.screen, MainScreen):
            raise ValueError("get_switch_slider_widget called outside of MainScreen")
        tab_to_determine_id = self.screen.query_exactly_one(TabbedContent).active
        if tab_to_determine_id == TabName.apply:
            return self.screen.query_one(
                IDS.apply.container.switch_slider_q, SwitchSlider
            )
        elif tab_to_determine_id == TabName.re_add:
            return self.screen.query_one(
                IDS.re_add.container.switch_slider_q, SwitchSlider
            )
        else:  # tab_to_determine_id == TabName.add
            return self.screen.query_one(
                IDS.add.container.switch_slider_q, SwitchSlider
            )

    #######################
    # Operate mode method #
    #######################

    def _toggle_operate_display(self, ids: AppIds) -> None:
        if isinstance(self.screen, InitChezmoi):
            init_left_side = self.screen.query_one(
                ids.container.left_side_q, FlatButtonsVertical
            )
            init_left_side.display = not init_left_side.display
            switch_slider = self.screen.query_one(
                ids.container.switch_slider_q, SwitchSlider
            )
            switch_slider.display = not switch_slider.display
        elif isinstance(self.screen, MainScreen):
            main_tabs = self.screen.query_exactly_one(Tabs)
            main_tabs.display = not main_tabs.display
            if ids.canvas_name in (TabName.apply, TabName.re_add):
                left_side = self.screen.query_one(
                    ids.container.left_side_q, TreeSwitcher
                )
                left_side.display = not left_side.display
                active_tab_widget = self._get_tab_widget()
                view_switcher_buttons = active_tab_widget.query(TabButtons).last()
                view_switcher_buttons.display = not view_switcher_buttons.display
            elif ids.canvas_name == TabName.add:
                left_side = self.screen.query_one(ids.container.left_side_q, Vertical)
                left_side.display = not left_side.display
            switch_slider = self.screen.query_one(
                ids.container.switch_slider_q, SwitchSlider
            )
            switch_slider.display = not switch_slider.display

    ############################
    # Message handling methods #
    ############################

    @on(ChangedPathsMsg)
    def handle_changed_paths_msg(self, msg: ChangedPathsMsg) -> None:
        self.notify(f"Changed paths: {sorted(msg.changed_paths)}")

    @on(OperateButtonMsg)
    def handle_operate_btn_msg(self, msg: OperateButtonMsg) -> None:
        operate_mode_container = self.screen.query_one(
            msg.ids.container.op_mode_q, OperateMode
        )
        if msg.button.btn_enum in (OpBtnLabel.cancel, OpBtnLabel.reload):
            operate_mode_container.display = False
            self._toggle_operate_display(msg.ids)
        elif msg.button.btn_enum in OpBtnEnum.review_btn_enums():
            operate_mode_container.btn_enum = msg.button.btn_enum
            operate_mode_container.display = True
            self._toggle_operate_display(msg.ids)
        elif msg.button.btn_enum in OpBtnEnum.run_btn_enums():
            operate_mode_container.btn_enum = msg.button.btn_enum

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
        if event.tabbed_content.active in (TabName.apply, TabName.re_add, TabName.add):
            slider: SwitchSlider = self._get_switch_slider_widget()
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
        self.changes_enabled = not self.changes_enabled
        self.screen.query_exactly_one(CustomHeader).changes_enabled = (
            self.changes_enabled
        )
        # do this before updating calling .update_review_info()
        CMD.run_cmd.changes_enabled = self.changes_enabled
        operate_mode_widgets = self.screen.query(OperateMode)
        for widget in operate_mode_widgets:
            if widget.display is True:
                widget.update_review_info()

    def action_toggle_switch_slider_visibility(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        slider: SwitchSlider = self._get_switch_slider_widget()
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

        if active_tab in (TabName.apply, TabName.re_add):
            active_tab_widget = self._get_tab_widget()
            view_switcher_buttons = active_tab_widget.query(TabButtons).last()

        if active_tab == TabName.apply:
            left_side = self.screen.query_one(
                IDS.apply.container.left_side_q, TreeSwitcher
            )
            operation_buttons = self.screen.query_one(
                IDS.apply.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.apply.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.re_add:
            left_side = self.screen.query_one(
                IDS.re_add.container.left_side_q, TreeSwitcher
            )
            operation_buttons = self.screen.query_one(
                IDS.re_add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.re_add.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.add:
            left_side = self.screen.query_one(IDS.add.container.left_side_q, Vertical)
            operation_buttons = self.screen.query_one(
                IDS.add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.add.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.logs:
            logs_tab_buttons = self.screen.query(TabButtons).last()
            logs_tab_buttons.display = (
                False if logs_tab_buttons.display is True else True
            )
        elif active_tab == TabName.config:
            left_side = self.screen.query_one(
                IDS.config.container.left_side_q, FlatButtonsVertical
            )
        elif active_tab == TabName.help:
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
                switch_slider = self._get_switch_slider_widget()
                if header.display is False or switch_slider.display is False:
                    return False
                active_tab = self.screen.query_exactly_one(TabbedContent).active
                return active_tab in (TabName.apply, TabName.re_add, TabName.add)
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

        if vertical:
            bars = cls.VERTICAL_BARS
        else:
            bars = cls.HORIZONTAL_BARS

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
