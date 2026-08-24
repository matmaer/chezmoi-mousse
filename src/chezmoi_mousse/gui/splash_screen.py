from __future__ import annotations

import asyncio
from collections import deque
from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual import events, getters, work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse import store
from chezmoi_mousse.cm_dataclasses import ManagedPaths
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import ColorVar, ReadCmd

from .common.ascii_constants import SPLASH_ASCII

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = ["SplashScreen"]


SPLASH_WIDTH = len(max(SPLASH_ASCII, key=len))
LOG_MSG_WIDTH = SPLASH_WIDTH - 13


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
            interval=0.1,
            callback=self._rotate_and_refresh,
            pause=True,
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

    def _forward_event(self, event: events.Event) -> None:
        # Override textual Screen method to prevent refresh when moving mouse
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
        # Allow all other events (keyboard, etc.)
        super()._forward_event(event)

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(markup=True))

    def on_mount(self) -> None:
        self.animated_fade = self.query_exactly_one(AnimatedFade)
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.width = "auto"
        self.splash_log.styles.height = len(ReadCmd)

        self.primary_color = self.app.get_color(ColorVar.text_primary)
        self.success_color = self.app.get_color(ColorVar.text_success)
        self.warning_color = self.app.get_color(ColorVar.text_warning)

        self.fade_timer = self.query_exactly_one(AnimatedFade).fade_timer
        self._run_all_tasks()

    def _get_log_msg(self, *, prefix: str, returncode: int | None) -> str:
        suffix = "completed"
        padding = LOG_MSG_WIDTH - (len(prefix) + len(suffix))
        if returncode is None:
            color = self.success_color
        elif returncode == 0:
            color = self.primary_color
        else:
            color = self.warning_color
        return f"[{color}]{prefix} {'.' * padding} {suffix}[/{color}]"

    def _run_chezmoi_command(self, command: ReadCmd) -> str:
        result: CommandResult = Commands.run_read_cmd(command, path_arg=None)
        msg = self._get_log_msg(prefix=result.pretty_cmd, returncode=result.returncode)
        return msg

    @work(thread=True)
    def _run_splash_cmd_worker(self, cmd: ReadCmd) -> None:
        msg = self._run_chezmoi_command(cmd)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True)
    def _run_managed_cmd_worker(self, cmd: ReadCmd) -> None:
        msg = self._run_chezmoi_command(cmd)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work
    async def _post_process_cmd_results(self) -> None:
        store.update_derived_vars()
        store.add_path = store.cfg.dest_dir
        store.apply_path = store.cfg.dest_dir
        store.re_add_path = store.cfg.dest_dir
        store.paths = ManagedPaths()
        msg = self._get_log_msg(prefix="process command outputs", returncode=None)
        self.splash_log.write(msg)

    @work
    async def _run_all_tasks(self) -> None:
        self.fade_timer.resume()

        # start splash workers first (contains chezmoi doctor, most expensive command)
        splash_workers = [
            self._run_splash_cmd_worker(cmd) for cmd in ReadCmd.splash_only_commands()
        ]
        # _post_process_cmd_results depends on these
        managed_cmd_workers = [
            self._run_managed_cmd_worker(cmd) for cmd in ReadCmd.managed_commands()
        ]

        # TODO: improve after store.py is fully implemented

        for worker in managed_cmd_workers:
            await worker.wait()
        for worker in splash_workers:
            await worker.wait()

        await self._post_process_cmd_results().wait()

        # Wait for the remaining tasks to finish
        # Only dismiss after a completed fade cycle
        while (
            self.animated_fade.step_count < 20
            or self.animated_fade.step_count % 20 != 0
        ):
            await asyncio.sleep(0.05)

        self.dismiss()
