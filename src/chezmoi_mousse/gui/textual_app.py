import dataclasses
from typing import ClassVar

from rich.color import Color
from rich.segment import Segment, Segments
from rich.style import Style
from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.scrollbar import ScrollBar, ScrollBarRender
from textual.theme import Theme
from textual.widgets import TabbedContent, TabPane, Tabs

from chezmoi_mousse.cm_attributes import CmAttributes
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import (
    BindingAction,
    BindingDescription,
    Chars,
    ColorVar,
    OpBtnLabel,
    TabLabel,
)

from .common.actionables import FlatButtonsVertical, SwitchSlider, TabButtons
from .common.managed_tree import DestDirTree
from .common.operate_modal import OperateModal
from .main_screen import CustomHeader, MainScreen
from .splash_screen import SplashScreen
from .tab_panes import AddTab, ApplyTab, ReAddTab

__all__ = ["ChezmoiGui"]


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

    SCREENS: ClassVar = {
        "main_screen": MainScreen,
        "operate_modal": lambda: OperateModal((OpBtnLabel.cancel,)),
    }

    cmattr: ClassVar[CmAttributes] = CmAttributes()

    def __init__(self) -> None:
        ScrollBar.renderer = CustomScrollBarRender  # monkey patch
        super().__init__()

    def _handle_exception(self, error: Exception) -> None:
        from chezmoi_mousse.debug.utils import DebugUtils

        DebugUtils.save_stacktrace()
        super()._handle_exception(error)

    def on_mount(self) -> None:
        self.register_theme(chezmoi_mousse_light)
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self._run_splash_screen()

    def get_color(self, color_var: ColorVar) -> str:
        return self.theme_variables.get(color_var.value, ColorVar.bogus.value)

    @work
    async def _run_splash_screen(self) -> None:
        await self.push_screen(SplashScreen(), callback=self._on_splash_dismiss)

    def _on_splash_dismiss(self, _: object) -> None:
        self.push_screen(MainScreen())

    ######################################################################
    # Helper methods for message handling and toggling widget visibility #
    ######################################################################

    def _get_tab_widget(self) -> TabPane:
        if not isinstance(self.screen, MainScreen):
            raise ValueError("get_tab_widget called outside of MainScreen")
        tab_pane = self.screen.query_exactly_one(TabbedContent).active_pane
        if tab_pane is None:
            raise ValueError("No active pane found in TabbedContent")
        return tab_pane

    def _get_switch_slider_widget(self) -> SwitchSlider | None:
        if not isinstance(self.screen, MainScreen):
            return None
        current_tab_widget = self._get_tab_widget()
        if isinstance(current_tab_widget, (ApplyTab, ReAddTab, AddTab)):
            return current_tab_widget.query_exactly_one(SwitchSlider)
        return None

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
            slider: SwitchSlider | None = self._get_switch_slider_widget()
            if slider is None:
                return
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

    def _update_binding_description(
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
        if not isinstance(self.screen, MainScreen):
            return
        Commands.live_run = not Commands.live_run
        new_description = (
            BindingDescription.switch_to_dry_run
            if Commands.live_run is True
            else BindingDescription.enable_live_run
        )
        self._update_binding_description(
            binding_action=BindingAction.toggle_dry_run, new_description=new_description
        )
        self.screen.query_exactly_one(CustomHeader).live_run = Commands.live_run

    def action_toggle_switch_slider(self) -> None:
        if not isinstance(self.screen, MainScreen):
            return
        slider: SwitchSlider | None = self._get_switch_slider_widget()
        if slider is None:
            return
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
        if not isinstance(self.screen, MainScreen):
            return
        active_tab = self.screen.query_exactly_one(TabbedContent).active
        left_side: DestDirTree | Vertical | FlatButtonsVertical | None = None
        operation_buttons = None
        switch_slider: SwitchSlider | None = self._get_switch_slider_widget()
        view_switcher_buttons = None

        header = self.screen.query_exactly_one(CustomHeader)
        header.display = not header.display
        main_tabs = self.screen.query_exactly_one(Tabs)
        main_tabs.display = not main_tabs.display

        if active_tab in (TabLabel.apply, TabLabel.re_add):
            active_tab_widget = self._get_tab_widget()
            view_switcher_buttons = active_tab_widget.query(TabButtons).last()

        if active_tab == TabLabel.apply:
            left_side = self.screen.query_one(
                self.cmattr.apply_id.container.left_side_q, DestDirTree
            )
            operation_buttons = self.screen.query_one(
                self.cmattr.apply_id.container.operate_buttons_q
            )
        elif active_tab == TabLabel.re_add:
            left_side = self.screen.query_one(
                self.cmattr.re_add_id.container.left_side_q, DestDirTree
            )
            operation_buttons = self.screen.query_one(
                self.cmattr.re_add_id.container.operate_buttons_q
            )
        elif active_tab == TabLabel.add:
            left_side = self.screen.query_one(
                self.cmattr.add_id.container.left_side_q, Vertical
            )
            operation_buttons = self.screen.query_one(
                self.cmattr.add_id.container.operate_buttons_q
            )
        elif active_tab == TabLabel.logs:
            logs_tab_buttons = self.screen.query(TabButtons).last()
            logs_tab_buttons.display = logs_tab_buttons.display is not True
        elif active_tab == TabLabel.config:
            left_side = self.screen.query_one(
                self.cmattr.config_id.container.left_side_q, FlatButtonsVertical
            )
        elif active_tab == TabLabel.debug:
            left_side = self.screen.query_one(
                self.cmattr.debug_id.container.left_side_q, FlatButtonsVertical
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
        self._update_binding_description(
            binding_action=BindingAction.toggle_maximized,
            new_description=new_description,
        )

    def check_action(
        self,
        action: str,
        parameters: tuple[object, ...],  # noqa: ARG002
    ) -> bool | None:
        if action == BindingAction.toggle_switch_slider:
            if isinstance(self.screen, MainScreen):
                header = self.screen.query_exactly_one(CustomHeader)
                switch_slider = self._get_switch_slider_widget()
                if (
                    switch_slider is None
                    or header.display is False
                    or switch_slider.display is False
                ):
                    return False
                active_tab = self.screen.query_exactly_one(TabbedContent).active
                return active_tab in (TabLabel.apply, TabLabel.re_add, TabLabel.add)
            return False

        elif action == BindingAction.toggle_maximized:
            if isinstance(self.screen, OperateModal):
                return False

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
