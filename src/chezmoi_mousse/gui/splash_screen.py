from __future__ import annotations

import asyncio
from collections import deque
from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual import events
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.reactive import reactive
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse.gui.common.ascii_constants import SPLASH_ASCII
from chezmoi_mousse.str_enums import ColorVar, LogStr, Tcss

if TYPE_CHECKING:
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = ["SplashScreen"]

SPLASH_WIDTH = len(max(SPLASH_ASCII, key=len))
LOG_MSG_WIDTH = SPLASH_WIDTH - 4


def _create_fade_line_styles() -> deque[Style]:
    start_color = "#0178D4"
    end_color = "#F187FB"
    fade: list[str] = [start_color] * 10
    gradient = Gradient.from_colors(start_color, end_color, quality=5)
    fade.extend([color.hex for color in gradient.colors])
    gradient.colors.reverse()
    fade.extend([color.hex for color in gradient.colors])
    fade_line_styles = deque(
        [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
    )
    return fade_line_styles


FADE_LINE_STYLES: deque[Style] = _create_fade_line_styles()


class AnimatedFade(Static):
    def on_mount(self) -> None:
        self.step_count = 0
        self.styles.height = len(SPLASH_ASCII)
        self.styles.width = SPLASH_WIDTH
        self.fade_timer = self.set_interval(
            name="refresh_self",
            interval=0.05,
            callback=self._rotate_and_refresh,
        )

    def _rotate_and_refresh(self) -> None:
        FADE_LINE_STYLES.rotate()
        self.step_count += 1
        self.refresh()

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH_ASCII[y], style=FADE_LINE_STYLES[y])])


class SplashScreen(Screen[None]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    log_message: reactive[str | None] = reactive(None, init=False)

    def _forward_event(self, event: events.Event) -> None:
        if isinstance(
            event,
            (
                events.AppBlur,
                events.AppFocus,
                events.CursorPosition,
                events.Enter,
                events.InputEvent,
                events.Leave,
                events.MouseEvent,
                events.Paste,
                events.Resize,
                events.TextSelected,
            ),
        ):
            return
        super()._forward_event(event)

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(markup=True, classes=Tcss.splash_log))

    async def on_mount(self) -> None:
        self.repo_existed = True
        self.color_map: dict[LogStr | int, str] = {
            LogStr.checked: self.app.theme_variables[ColorVar.warning],
            LogStr.decoded: self.app.theme_variables[ColorVar.success],
            LogStr.missing: self.app.theme_variables[ColorVar.error],
            LogStr.present: self.app.theme_variables[ColorVar.foreground_darken_2],
            LogStr.reports: self.app.theme_variables[ColorVar.accent_darken_3],
            LogStr.success: self.app.theme_variables[ColorVar.text_primary],
            LogStr.trigger: self.app.theme_variables[ColorVar.text_accent],
        }
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.width = LOG_MSG_WIDTH
        self.animated_fade = self.query_exactly_one(AnimatedFade)

    async def write_log_msg(
        self,
        *,
        prefix_suffix: tuple[str, LogStr] | None = None,
        cmd_result: CommandResult | None = None,
    ) -> None:
        if prefix_suffix:
            prefix = prefix_suffix[0]
            suffix = prefix_suffix[1]
        elif cmd_result:
            prefix = cmd_result.pretty_cmd
            suffix = LogStr.success if cmd_result.returncode == 0 else LogStr.checked
        else:
            self.notify("Nothing to log for splash screen.", severity="error")
            return

        dots_count = LOG_MSG_WIDTH - len(prefix) - len(suffix) - 4
        dots = "." * dots_count
        color = self.color_map[suffix]
        msg = f"[{color}]{prefix} {dots} {suffix}[/{color}]"
        self.splash_log.write(msg)

    async def dismiss_after_fade_loop(self) -> None:
        while (
            self.animated_fade.step_count < 20
            or self.animated_fade.step_count % 20 != 0
        ):
            await asyncio.sleep(0.08)
        self.dismiss()
