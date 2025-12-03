import dataclasses
from math import ceil
from typing import TYPE_CHECKING

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual import work
from textual.app import App
from textual.binding import Binding
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import TabbedContent, Tabs
from textual.worker import WorkerCancelled

from chezmoi_mousse import (
    BindingAction,
    BindingDescription,
    Chars,
    OperateData,
    ScreenIds,
    TabIds,
    TabName,
)
from chezmoi_mousse.shared import (
    ContentsView,
    CustomHeader,
    DiffView,
    FlatButtonsVertical,
    GitLogPath,
    LogsTabButtons,
    ViewTabButtons,
)

from .init_screen import InitScreen
from .install_help import InstallHelp
from .main_tabs import MainScreen
from .operate import OperateInfo, OperateScreen
from .splash import SplashScreen
from .tabs.add_tab import AddTab, FilteredDirTree
from .tabs.common.switch_slider import SwitchSlider
from .tabs.common.switchers import TreeSwitcher, ViewSwitcher
from .tabs.common.trees import TreeBase

if TYPE_CHECKING:
    from chezmoi_mousse import Chezmoi, PreRunData, SplashData

__all__ = ["ChezmoiGUI"]

# TODO: implement 'chezmoi verify', if exit 0, display message in Tree
# widgets inform the user why the Tree widget is empty.
# TODO: implement spinner for commands taking a bit longer like operations.

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

    BINDINGS = [
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
            action=BindingAction.toggle_switch_slider,
            description=BindingDescription.hide_filters,
        ),
        Binding(
            key="D,d",
            action=BindingAction.toggle_dry_run,
            description=BindingDescription.remove_dry_run_flag,
        ),
    ]

    CSS_PATH = "gui.tcss"

    SCREENS = {
        "init": InitScreen,
        "install_help": InstallHelp,
        "splash": SplashScreen,
    }

    def __init__(self, pre_run_data: "PreRunData") -> None:
        self.chezmoi: "Chezmoi"
        self.screen_ids = ScreenIds()
        self.tab_ids = TabIds()

        self.pre_run_data: "PreRunData" = pre_run_data
        self.chezmoi_found: bool = self.pre_run_data.chezmoi_found
        self.dev_mode: bool = self.pre_run_data.dev_mode
        self.force_init_screen: bool = self.pre_run_data.force_init_screen

        # Manage state between screens
        self.changes_enabled: bool = False
        self.operate_data: "OperateData | None" = None
        self.splash_data: "SplashData | None" = None

        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.start_app_with_splash_screen()

    @work
    async def start_app_with_splash_screen(self) -> None:
        # Run splash screen once to gather command outputs
        try:
            splash_screen_worker = self.push_splash_screen()
            await splash_screen_worker.wait()
        except WorkerCancelled:
            # User exited during splash screen, exit cleanly
            return
        # Chezmoi command not found, SplashScreen will return None
        if splash_screen_worker.result is None:
            self.push_screen("install_help")
            return
        # Chezmoi found but cat_config fails OR force_init_screen flag is set
        if (
            splash_screen_worker.result.cat_config.returncode != 0
            or self.force_init_screen
        ):
            self.force_init_screen = False  # Reset force_init_screen for dev.
            try:
                self.splash_data = splash_screen_worker.result
                init_worker = self.push_init_screen()
                await init_worker.wait()
                # After init screen, re-run splash screen to load all data
                try:
                    splash_screen_worker = self.push_splash_screen()
                    await splash_screen_worker.wait()
                except WorkerCancelled:
                    # User exited during second splash screen, exit cleanly
                    return
                self.push_main_screen(
                    splash_data=splash_screen_worker.result,
                    operate_data=init_worker.result,
                )
                return
            except WorkerCancelled:
                # User exited during init screen, exit cleanly
                return
        # Chezmoi found, init not needed
        self.push_main_screen(splash_data=splash_screen_worker.result)

    @work
    async def push_splash_screen(self) -> "SplashData | None":
        return await self.push_screen("splash", wait_for_dismiss=True)

    @work
    async def push_init_screen(self) -> "OperateData | None":
        return await self.push_screen(InitScreen(), wait_for_dismiss=True)

    @work
    async def push_main_screen(
        self,
        *,
        splash_data: "SplashData | None",
        operate_data: "OperateData | None" = None,
    ) -> None:
        if splash_data is None:
            raise ValueError("splash_data is None after running SplashScreen")
        dest_dir = splash_data.parsed_config.dest_dir
        AddTab.destDir = dest_dir
        ContentsView.destDir = dest_dir
        DiffView.destDir = dest_dir
        GitLogPath.destDir = dest_dir
        MainScreen.destDir = dest_dir
        TreeBase.destDir = dest_dir
        ViewSwitcher.destDir = dest_dir

        OperateInfo.git_autocommit = splash_data.parsed_config.git_autocommit
        OperateInfo.git_autopush = splash_data.parsed_config.git_autopush

        self.push_screen(
            MainScreen(splash_data=splash_data, operate_data=operate_data)
        )

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        if event.tabbed_content.active in (
            TabName.apply,
            TabName.re_add,
            TabName.add,
        ):
            self.update_toggle_switch_slider_binding()
            self.refresh_bindings()

    def get_switch_slider_widget(self) -> SwitchSlider:
        active_tab = self.screen.query_exactly_one(TabbedContent).active
        if active_tab == TabName.apply:
            slider = self.screen.query_one(
                self.tab_ids.apply.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.re_add:
            slider = self.screen.query_one(
                self.tab_ids.re_add.container.switch_slider_q, SwitchSlider
            )
        else:  # active_tab == TabName.add
            slider = self.screen.query_one(
                self.tab_ids.add.container.switch_slider_q, SwitchSlider
            )
        return slider

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

    def update_toggle_switch_slider_binding(self) -> None:
        slider: SwitchSlider = self.get_switch_slider_widget()
        slider_visible = slider.has_class("-visible")
        new_description = (
            BindingDescription.hide_filters
            if slider_visible is False
            else BindingDescription.show_filters
        )
        self.update_binding_description(
            binding_action=BindingAction.toggle_switch_slider,
            new_description=new_description,
        )

    def action_toggle_dry_run(self) -> None:
        # All this will also run for the InitScreen except the OperateInfo part
        self.changes_enabled = not self.changes_enabled
        reactive_header = self.screen.query_exactly_one(CustomHeader)
        reactive_header.changes_enabled = self.changes_enabled

        if isinstance(self.screen, OperateScreen):
            operate_info = self.screen.query_exactly_one(OperateInfo)
            operate_info.write_info_lines()

        new_description = (
            BindingDescription.add_dry_run_flag
            if self.changes_enabled is True
            else BindingDescription.remove_dry_run_flag
        )
        self.update_binding_description(
            binding_action=BindingAction.toggle_dry_run,
            new_description=new_description,
        )

    def action_toggle_switch_slider(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        slider: SwitchSlider = self.get_switch_slider_widget()
        slider.toggle_class("-visible")
        self.update_toggle_switch_slider_binding()

    def action_toggle_maximized(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        active_tab = self.screen.query_exactly_one(TabbedContent).active
        left_side = None
        operation_buttons = None
        switch_slider = None
        view_switcher_buttons = None

        header = self.screen.query_exactly_one(CustomHeader)
        header.display = False if header.display is True else True
        main_tabs = self.screen.query_exactly_one(Tabs)
        main_tabs.display = False if main_tabs.display is True else True

        if active_tab == TabName.apply:
            left_side = self.screen.query_one(
                self.tab_ids.apply.container.left_side_q, TreeSwitcher
            )
            operation_buttons = self.screen.query_one(
                self.tab_ids.apply.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                self.tab_ids.apply.container.switch_slider_q, SwitchSlider
            )
            view_switcher_buttons = self.screen.query_one(
                self.tab_ids.apply.switcher.view_buttons_q, ViewTabButtons
            )
        elif active_tab == TabName.re_add:
            left_side = self.screen.query_one(
                self.tab_ids.re_add.container.left_side_q, TreeSwitcher
            )
            operation_buttons = self.screen.query_one(
                self.tab_ids.re_add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                self.tab_ids.re_add.container.switch_slider_q, SwitchSlider
            )
            view_switcher_buttons = self.screen.query_one(
                self.tab_ids.re_add.switcher.view_buttons_q, ViewTabButtons
            )
        elif active_tab == TabName.add:
            left_side = self.screen.query_one(
                self.tab_ids.add.tree.dir_tree_q, FilteredDirTree
            )
            operation_buttons = self.screen.query_one(
                self.tab_ids.add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                self.tab_ids.add.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.logs:
            logs_tab_buttons = self.screen.query_one(
                self.tab_ids.logs.switcher.logs_tab_buttons_q, LogsTabButtons
            )
            logs_tab_buttons.display = (
                False if logs_tab_buttons.display is True else True
            )
        elif active_tab == TabName.config:
            left_side = self.screen.query_one(
                self.tab_ids.config.container.left_side_q, FlatButtonsVertical
            )
        elif active_tab == TabName.help:
            left_side = self.screen.query_one(
                self.tab_ids.help.container.left_side_q, FlatButtonsVertical
            )

        if left_side is not None:
            left_side.display = False if left_side.display is True else True
        if operation_buttons is not None:
            operation_buttons.display = (
                False if operation_buttons.display is True else True
            )
        if view_switcher_buttons is not None:
            view_switcher_buttons.display = (
                False if view_switcher_buttons.display is True else True
            )
        if switch_slider is not None:
            switch_slider.display = (
                False if switch_slider.display is True else True
            )

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
        if isinstance(self.screen, (InstallHelp, InitScreen)):
            self.exit()
        elif isinstance(self.screen, OperateScreen):
            self.screen.dismiss(self.operate_data)

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == BindingAction.exit_screen:
            if isinstance(
                self.screen, (InstallHelp, InitScreen, OperateScreen)
            ):
                return True
            else:
                return False
        elif action == BindingAction.toggle_switch_slider:
            if isinstance(self.screen, MainScreen):
                header = self.screen.query_exactly_one(CustomHeader)
                if header.display is False:
                    return False
                active_tab = self.screen.query_exactly_one(
                    TabbedContent
                ).active
                if active_tab == TabName.apply:
                    return True
                elif active_tab == TabName.re_add:
                    return True
                elif active_tab == TabName.add:
                    return True
                elif active_tab == TabName.logs:
                    return False
                elif active_tab == TabName.config:
                    return False
                elif active_tab == TabName.help:
                    return False
            else:
                return False
        elif action == BindingAction.toggle_dry_run:
            if isinstance(self.screen, MainScreen):
                header = self.screen.query_exactly_one(CustomHeader)
                if header.display is False:
                    return False
                active_tab = self.screen.query_exactly_one(
                    TabbedContent
                ).active
                if active_tab == TabName.apply:
                    return True
                elif active_tab == TabName.re_add:
                    return True
                elif active_tab == TabName.add:
                    return True
                elif active_tab == TabName.logs:
                    return False
                elif active_tab == TabName.config:
                    return False
                elif active_tab == TabName.help:
                    return False
            elif isinstance(self.screen, (OperateScreen, InitScreen)):
                return True
            else:
                return False
        elif action == BindingAction.toggle_maximized:
            if isinstance(
                self.screen, (InitScreen, InstallHelp, OperateScreen)
            ):
                return False
        return True


class CustomScrollBarRender(ScrollBarRender):
    # Used to monkey patch the textual ScrollBar.renderer method in ChezmoiGUI
    # __init__

    @classmethod
    def render_bar(
        cls,
        size: int = 25,
        virtual_size: float = 50,
        window_size: float = 20,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        back_color: Color = Color.parse("#555555"),
        bar_color: Color = Color.parse("bright_magenta"),
    ) -> Segments:
        if vertical:
            bars = cls.VERTICAL_BARS
        else:
            bars = cls.HORIZONTAL_BARS

        back = back_color
        bar = bar_color

        len_bars = len(bars)
        width_thickness = thickness if vertical else 1

        _Segment = Segment
        _Style = Style
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

            upper_back_segment = Segment(
                blank, _Style(bgcolor=back, meta=upper)
            )
            lower_back_segment = Segment(
                blank, _Style(bgcolor=back, meta=lower)
            )

            segments = [upper_back_segment] * int(size)
            segments[end_index:] = [lower_back_segment] * (size - end_index)
            if vertical:
                segments[start_index:end_index] = [
                    _Segment(
                        blank,
                        _Style(color=bar, reverse=True, meta=foreground_meta),
                    )
                ] * (end_index - start_index)
                if start_index < len(segments):
                    bar_character = bars[len_bars - 1 - start_bar]
                    if bar_character != " ":
                        segments[start_index] = _Segment(
                            bar_character * width_thickness,
                            (
                                _Style(
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
                                )
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
                                    bgcolor=back,
                                    color=bar,
                                    meta=foreground_meta,
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
            return Segments(
                (segments + [_Segment.line()]) * thickness, new_lines=False
            )
