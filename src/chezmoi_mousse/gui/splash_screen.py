from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual import events, getters, work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.geometry import Region
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse import ReadCmd

if TYPE_CHECKING:
    from chezmoi_mousse.chezmoi_command import CommandResult
    from chezmoi_mousse.type_checking import ChezmoiGui

__all__ = ["SplashScreen"]

SPLASH_LOGO = """\
 _______________________________ ___________________._
|       |   |   |    ___|___    |    '    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
"""

SPLASH = SPLASH_LOGO.replace("===", "=\u200b=\u200b=").splitlines()

FADE_HEIGHT = len(SPLASH)
FADE_WIDTH = len(max(SPLASH, key=len))
LOG_MSG_WIDTH = 44


class AnimatedFade(Static):

    def on_mount(self) -> None:
        self.styles.height = FADE_HEIGHT
        self.styles.width = FADE_WIDTH
        start_color = "#0178D4"
        end_color = "#F187FB"
        fade = [start_color] * 8
        gradient = Gradient.from_colors(start_color, end_color, quality=6)
        fade.extend([color.hex for color in gradient.colors])
        gradient.colors.reverse()
        fade.extend([color.hex for color in gradient.colors])
        self.fade_line_styles = deque(
            [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
        )
        self.fade_line_styles.rotate(-2)
        self.set_interval(name="refresh_self", interval=0.1, callback=self.refresh)

    def render_lines(self, crop: Region) -> list[Strip]:
        self.fade_line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.fade_line_styles[y])])


class SplashLog(RichLog):

    def on_mount(self) -> None:
        self.styles.height = (
            len(ReadCmd.splash_commands()) + 1
        )  # +1 for parse dump-config log
        self.styles.width = "auto"
        self.styles.margin = 2
        self.markup = True


class SplashScreen(Screen[None]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def _forward_event(self, event: events.Event) -> None:
        # Override textual Screen method
        # Skip all mouse events to prevent interference with animation
        if isinstance(event, events.MouseEvent):
            return
        # Allow all other events (keyboard, etc.)
        super()._forward_event(event)

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(SplashLog())

    def on_mount(self) -> None:
        self.set_interval(interval=2, callback=self._all_workers_finished)
        self.splash_log = self.query_exactly_one(SplashLog)
        for splash_cmd in ReadCmd.splash_commands():
            self._run_io_worker(splash_cmd)

    def _get_log_message(self, color: str, prefix: str, suffix: str) -> str:
        padding = LOG_MSG_WIDTH - (len(prefix) + len(suffix))
        return f"[{color}]{prefix} {'.' * padding} {suffix}[/{color}]"

    @work(group="splash_worker")
    async def _parse_json(
        self, result: CommandResult, read_cmd: ReadCmd, short_cmd: str
    ) -> str:
        prefix = f"parse {short_cmd}"
        parsed_json = json.loads(result.std_out)
        try:
            if read_cmd == ReadCmd.dump_config:
                self.app.cm_attr.cfg = parsed_json
            elif read_cmd == ReadCmd.template_data:
                self.app.cm_attr.template_data = parsed_json
            suffix = "success"
            color = self.app.theme_variables["text-success"]
        except json.JSONDecodeError:
            suffix = "failed"
            color = self.app.theme_variables["text-error"]
        return self._get_log_message(color, prefix, suffix)

    @work(group="splash_worker")
    def _run_chezmoi_command(self, splash_cmd: ReadCmd, short_cmd: str) -> None:
        result = self.app.cm_attr.command.run(splash_cmd)
        color = self.app.theme_variables["text-primary"]
        suffix = "unknown"
        if result.returncode == 0:
            suffix = "success"
        else:
            suffix = "checked"
            color = self.app.theme_variables["text-warning"]
        msg = self._get_log_message(color, short_cmd, suffix)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group="splash_worker")
    def _run_io_worker(self, splash_cmd: ReadCmd) -> None:
        result: CommandResult = self.app.cm_attr.command.run(splash_cmd)
        short_cmd = result.pretty_cmd.replace("chezmoi", "")
        log_text = self._run_chezmoi_command(result, short_cmd).wait()
        self.app.call_from_thread(self.splash_log.write, log_text)
        if splash_cmd in (ReadCmd.dump_config, ReadCmd.dump_config):
            log_text = self._parse_json(result, short_cmd).wait()
            self.app.call_from_thread(self.splash_log.write, log_text)

    def _all_workers_finished(self) -> None:
        # TODO: also update cm_attributes
        if all(
            worker.is_finished
            for worker in self.workers
            if worker.group == "splash_worker"
        ):
            self.dismiss()
