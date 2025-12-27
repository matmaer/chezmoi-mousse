import dataclasses
from math import ceil
from typing import TYPE_CHECKING

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import Button, Static, TabbedContent, Tabs

from chezmoi_mousse import (
    IDS,
    AppState,
    BindingAction,
    BindingDescription,
    Chars,
    OpBtnEnum,
    OpBtnLabels,
    OperateStrings,
    TabName,
)
from chezmoi_mousse.shared import (
    CustomHeader,
    FlatButtonsVertical,
    LogsTabButtons,
    OperateButtonMsg,
    ViewTabButtons,
)

from .install_help import InstallHelpScreen
from .main_tabs import MainScreen
from .operate_init import OperateInitScreen
from .splash import SplashScreen
from .tabs.add_tab import AddTab, FilteredDirTree
from .tabs.apply_tab import ApplyTab
from .tabs.common.switch_slider import SwitchSlider
from .tabs.common.switchers import TreeSwitcher
from .tabs.re_add_tab import ReAddTab

if TYPE_CHECKING:
    from chezmoi_mousse import (
        ChezmoiCommand,
        ChezmoiPaths,
        CommandResult,
        SplashData,
    )

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
            "ctrl+q",
            action="quit",
            description="Quit",
            tooltip="Quit the app and return to the command prompt.",
            show=True,
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
            action=BindingAction.toggle_switch_slider,
            description=BindingDescription.hide_filters,
        ),
        Binding(
            key="D,d",
            action=BindingAction.toggle_dry_run,
            description=BindingDescription.toggle_dry_run,
        ),
    ]

    CSS_PATH = "gui.tcss"
    changes_enabled: reactive[bool] = reactive(False)

    def __init__(
        self, *, chezmoi_found: bool, dev_mode: bool, pretend_init_needed: bool
    ) -> None:
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()
        AppState.set_app(self)

        self.cmd: "ChezmoiCommand"
        self.paths: "ChezmoiPaths"

        self.chezmoi_found: bool = chezmoi_found
        self.dev_mode: bool = dev_mode
        self.force_init_needed: bool = pretend_init_needed
        self.init_needed: bool = False
        self.current_op_btn_msg: OperateButtonMsg | None = None

        # Disable Maxdmize/Minimize and Show/Hide Filters bindings when
        # in operate mode in the MainScreen
        self.operating_mode: bool = False

        # Manage state between screens
        self.init_cmd_result: "CommandResult | None" = None
        self.operate_cmd_result: "CommandResult | None" = None
        self.splash_data: "SplashData | None" = None

        self.git_autocommit: bool | None = None
        self.git_autopush: bool | None = None

        # Arbitrary max file size used by FilteredDirTree and ContentsView but
        # should be reasonable truncate for files to be considered as dotfiles.
        # TODO: make this configurable
        self.max_file_size: int = 500 * 1024  # 500 KiB

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.run_splash_screen()

    @work
    async def run_splash_screen(self) -> None:
        # Run splash screen once to gather command outputs
        await self.push_screen(SplashScreen(), wait_for_dismiss=True)
        if self.splash_data is None:
            # Chezmoi command not found, SplashScreen will return None
            self.push_screen(InstallHelpScreen())
            return
        if self.init_needed is True:
            await self.push_screen(OperateInitScreen(), wait_for_dismiss=True)
            await self.push_screen(SplashScreen(), wait_for_dismiss=True)
        self.push_screen(MainScreen())

    def toggle_widget_visibility(
        self, tab_widget: ApplyTab | ReAddTab, btn_qid: str
    ) -> None:
        self.toggle_main_tabs_display()
        left_side = tab_widget.query_one(
            tab_widget.ids.container.left_side_q, TreeSwitcher
        )
        left_side.display = False if left_side.display is True else True
        view_switcher_buttons = tab_widget.query_one(
            tab_widget.ids.switcher.view_buttons_q, ViewTabButtons
        )
        view_switcher_buttons.display = (
            False if view_switcher_buttons.display is True else True
        )
        operate_info_widget = self.get_operate_info_widget()
        operate_info_widget.display = (
            True if operate_info_widget.display is False else False
        )
        all_buttons = tab_widget.query(Button)
        switch_slider = self.get_switch_slider_widget()
        op_btn_widget = tab_widget.query_one(btn_qid, Button)
        if self.operating_mode is True:
            for btn in all_buttons:
                if btn is tab_widget.exit_btn or btn is op_btn_widget:
                    btn.display = True
                else:
                    btn.display = False
            switch_slider.display = False  # regardless of visibility
        else:
            # When exiting operating mode, show all operation buttons, hide exit button
            for btn in all_buttons:
                if btn is tab_widget.exit_btn:
                    btn.display = False
                else:
                    btn.display = True
            # this will restore the previous vilibility, whatever it was
            switch_slider.display = True

    def write_pre_operate_info(
        self, *, tab_widget: ApplyTab | ReAddTab
    ) -> None:
        if self.current_op_btn_msg is None:
            raise ValueError(
                "current_op_review_msg is None in write_pre_operate_info"
            )
        lines_to_write: list[str] = []
        if tab_widget.current_node is None:
            raise ValueError("current_node is None in write_pre_operate_info")
        lines_to_write.append(
            f"{OperateStrings.ready_to_run}"
            f"[$text-warning]{self.current_op_btn_msg.btn_enum.write_cmd.pretty_cmd} "
            f"{tab_widget.current_node.path}[/]"
        )
        if self.changes_enabled is True:
            if self.splash_data is None:
                raise ValueError(
                    "splash_data is None in write_pre_operate_info"
                )
            if self.splash_data.parsed_config.git_autocommit is True:
                lines_to_write.append(OperateStrings.auto_commit)
            if self.splash_data.parsed_config.git_autopush is True:
                lines_to_write.append(OperateStrings.auto_push)
        operate_info = self.get_operate_info_widget()
        operate_info.border_subtitle = OperateStrings.re_add_subtitle
        operate_info.update("\n".join(lines_to_write))

    @on(OperateButtonMsg)
    def handle_button_pressed(self, msg: OperateButtonMsg) -> None:
        if not isinstance(self.screen, MainScreen) or msg.canvas_name not in (
            TabName.apply,
            TabName.re_add,
        ):
            return
        self.current_op_btn_msg = msg
        tabbed_content = self.screen.query_exactly_one(TabbedContent)
        if msg.canvas_name == TabName.apply:
            tab_widget = tabbed_content.query_one(msg.tab_qid, ApplyTab)
            op_btn_widget = tab_widget.query_one(msg.btn_qid, Button)
            review_label = OpBtnLabels.apply_review
        elif msg.canvas_name == TabName.re_add:
            tab_widget = tabbed_content.query_one(msg.tab_qid, ReAddTab)
            op_btn_widget = tab_widget.query_one(msg.btn_qid, Button)
            review_label = OpBtnLabels.re_add_review
        else:
            self.notify(
                f"OperateButtonMsg received for unsupported tab: {msg.canvas_name}"
            )
            return
        review_to_run = {
            OpBtnLabels.apply_review.value: OpBtnLabels.apply_run.value,
            OpBtnLabels.re_add_review.value: OpBtnLabels.re_add_run.value,
            OpBtnLabels.destroy_review.value: OpBtnLabels.destroy_run.value,
            OpBtnLabels.forget_review.value: OpBtnLabels.forget_run.value,
        }
        if msg.label in review_to_run.values():
            tab_widget.run_operate_command(msg.btn_enum)
        else:
            if msg.label in review_to_run:
                # Update state BEFORE toggling visibility
                self.operating_mode = True
                op_btn_widget.label = review_to_run[msg.label]
                self.write_pre_operate_info(tab_widget=tab_widget)
            elif msg.label == OpBtnLabels.cancel:
                self.operating_mode = False
                op_btn_widget.disabled = False
                op_btn_widget.label = review_label
            elif msg.label == OpBtnLabels.reload:
                self.operating_mode = False
            # Toggle visibility AFTER updating operating_mode and labels
            self.toggle_widget_visibility(
                tab_widget=tab_widget, btn_qid=msg.btn_qid
            )

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        if event.tabbed_content.active in (
            TabName.apply,
            TabName.re_add,
            TabName.add,
        ):
            self.update_switch_slider_binding()
            self.refresh_bindings()

    def toggle_main_tabs_display(self) -> None:
        main_tabs = self.screen.query_exactly_one(Tabs)
        main_tabs.display = False if main_tabs.display is True else True

    def get_operate_info_widget(self) -> Static:
        if not isinstance(self.screen, MainScreen):
            raise ValueError(
                "get_operate_info_widget called outside of MainScreen"
            )
        active_tab = self.screen.query_exactly_one(TabbedContent).active
        if active_tab == TabName.apply:
            return self.screen.query_one(
                IDS.apply.static.operate_info_q, Static
            )
        if active_tab == TabName.re_add:
            return self.screen.query_one(
                IDS.re_add.static.operate_info_q, Static
            )
        else:  # active_tab == TabName.add
            return self.screen.query_one(IDS.add.static.operate_info_q, Static)

    def get_switch_slider_widget(self) -> SwitchSlider:
        if not isinstance(self.screen, MainScreen):
            raise ValueError(
                "get_switch_slider_widget called outside of MainScreen"
            )
        active_tab = self.screen.query_exactly_one(TabbedContent).active
        if active_tab == TabName.apply:
            return self.screen.query_one(
                IDS.apply.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.re_add:
            return self.screen.query_one(
                IDS.re_add.container.switch_slider_q, SwitchSlider
            )
        else:  # active_tab == TabName.add
            return self.screen.query_one(
                IDS.add.container.switch_slider_q, SwitchSlider
            )

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

    def update_switch_slider_binding(self) -> None:
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
        AppState.set_changes_enabled(not self.changes_enabled)
        reactive_header = self.screen.query_exactly_one(CustomHeader)
        reactive_header.changes_enabled = self.changes_enabled
        if isinstance(self.screen, (OperateInitScreen)):
            self.screen.update_operate_info()
        elif isinstance(self.screen, MainScreen):
            if self.operating_mode is False:
                return
            add_tab = self.screen.query_exactly_one(AddTab)
            add_tab.write_pre_operate_info(OpBtnEnum.add_file)

            apply_tab = self.screen.query_exactly_one(ApplyTab)
            self.write_pre_operate_info(tab_widget=apply_tab)
            re_add_tab = self.screen.query_exactly_one(ReAddTab)
            self.write_pre_operate_info(tab_widget=re_add_tab)

    def action_toggle_switch_slider(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        slider: SwitchSlider = self.get_switch_slider_widget()
        slider.toggle_class("-visible")
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
        self.toggle_main_tabs_display()

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
            view_switcher_buttons = self.screen.query_one(
                IDS.apply.switcher.view_buttons_q, ViewTabButtons
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
            view_switcher_buttons = self.screen.query_one(
                IDS.re_add.switcher.view_buttons_q, ViewTabButtons
            )
        elif active_tab == TabName.add:
            left_side = self.screen.query_one(
                IDS.add.tree.dir_tree_q, FilteredDirTree
            )
            operation_buttons = self.screen.query_one(
                IDS.add.container.operate_buttons_q
            )
            switch_slider = self.screen.query_one(
                IDS.add.container.switch_slider_q, SwitchSlider
            )
        elif active_tab == TabName.logs:
            logs_tab_buttons = self.screen.query_one(
                IDS.logs.switcher.logs_tab_buttons_q, LogsTabButtons
            )
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
        self.screen.dismiss()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action == BindingAction.toggle_switch_slider:
            if isinstance(self.screen, MainScreen):
                if self.operating_mode is True:
                    return None
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
            elif isinstance(self.screen, (OperateInitScreen)):
                return True
            else:
                return False
        elif action == BindingAction.toggle_maximized:
            if self.operating_mode is True:
                return None
            if isinstance(self.screen, (InstallHelpScreen, OperateInitScreen)):
                return False
        elif action == BindingAction.exit_screen:
            if isinstance(
                self.screen, (InstallHelpScreen, MainScreen, SplashScreen)
            ):
                return False
            elif isinstance(self.screen, OperateInitScreen):
                if self.init_cmd_result is None:
                    return None
                elif self.init_cmd_result.dry_run is True:
                    return None
                elif self.init_cmd_result.dry_run is False:
                    return True
                else:
                    return None
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
