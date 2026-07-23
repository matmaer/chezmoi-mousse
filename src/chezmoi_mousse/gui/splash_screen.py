from __future__ import annotations

import json
from collections import deque
from enum import StrEnum, auto
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

from chezmoi_mousse.cm_attributes import CmAttrFunctions
from chezmoi_mousse.cm_command import CommandResult, ReadCmd

if TYPE_CHECKING:
    from chezmoi_mousse.cm_type_checking import ChezmoiGui

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

# +1 to update cm_attr.managed
LOG_HEIGHT = len(ReadCmd.splash_cmd_group()) + len(ReadCmd.json_output_cmd_group()) + 1


class SplashWorker(StrEnum):
    cm_attr_group = auto()
    managed_cmd_group = auto()
    splash_cmd_group = auto()


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
        self.fade_timer = self.set_interval(
            name="refresh_self", interval=0.1, callback=self.refresh, pause=True
        )

    def render_lines(self, crop: Region) -> list[Strip]:
        self.fade_line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.fade_line_styles[y])])


class SplashLog(RichLog):

    def __init__(self) -> None:
        super().__init__(markup=True)

    def on_mount(self) -> None:
        self.styles.width = "auto"
        self.styles.margin = 2
        self.styles.height = LOG_HEIGHT


class SplashScreen(Screen[None]):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def _forward_event(self, event: events.Event) -> None:
        # Override textual Screen method to prevent refresh when moving mouse
        if isinstance(event, events.MouseEvent):
            return
        # Allow all other events (keyboard, etc.)
        super()._forward_event(event)

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(SplashLog())

    def on_mount(self) -> None:
        fade_timer = self.query_exactly_one(AnimatedFade).fade_timer
        self.cm_attr_managed_updated = False
        self.cm_attr_parsed_json_updated = False
        self.primary_color = self.app.theme_variables["text-primary"]
        self.warning_color = self.app.theme_variables["text-warning"]
        self.error_color = self.app.theme_variables["text-error"]
        self.splash_log = self.query_exactly_one(SplashLog)
        for command in ReadCmd.managed_cmd_group():
            self._run_managed_cmd(command)
        for command in ReadCmd.splash_cmd_group():
            self._run_splash_cmd(command)
        fade_timer.resume()
        self.set_interval(interval=2, callback=self._all_workers_finished)

    def _get_log_msg(self, prefix: str, returncode: int) -> str:
        if "parse" in prefix:
            suffix = "failed"
            color = self.error_color
        suffix = "done"
        padding = LOG_MSG_WIDTH - (len(prefix) + len(suffix))
        color = self.primary_color if returncode == 0 else self.warning_color
        return f"[{color}]{prefix} {'.' * padding} {suffix}[/{color}]"

    @work(thread=True, group=SplashWorker.splash_cmd_group)
    async def _run_splash_cmd(self, command: ReadCmd) -> None:
        result: CommandResult = self.app.cm_attr.command.run(command)
        msg = self._get_log_msg(command.pretty_cmd, result.returncode)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group=SplashWorker.managed_cmd_group)
    async def _run_managed_cmd(self, command: ReadCmd) -> None:
        result: CommandResult = self.app.cm_attr.command.run(command)
        msg = self._get_log_msg(command.pretty_cmd, result.returncode)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group=SplashWorker.cm_attr_group)
    def _update_cm_attr_parsed_json(self) -> None:
        try:
            CmAttrFunctions.json_loads_outputs()
            returncode = 0
        except json.JSONDecodeError:
            returncode = 1
        self.cm_attr_parsed_json_updated = True
        msg_1 = self._get_log_msg("parse dump-config", returncode)
        msg_2 = self._get_log_msg("parse template_data", returncode)
        self.app.call_from_thread(self.splash_log.write, msg_1)
        self.app.call_from_thread(self.splash_log.write, msg_2)

    @work(thread=True, group=SplashWorker.cm_attr_group)
    def _update_cm_attr_managed(self) -> None:

        CmAttrFunctions.update_managed_attr()
        self.cm_attr_managed_updated = True
        msg = self._get_log_msg("update cm_attr.managed", returncode=0)
        self.app.call_from_thread(self.splash_log.write, msg)

    def _worker_group_finished(self, worker_group: SplashWorker) -> bool:
        group_workers = (w for w in self.workers if w.group == worker_group)
        return all(worker.is_finished for worker in group_workers)

    def _all_workers_finished(self) -> None:
        if (
            self._worker_group_finished(SplashWorker.splash_cmd_group)
            and self.cm_attr_parsed_json_updated is False
        ):
            self._update_cm_attr_parsed_json()
        elif (
            self._worker_group_finished(SplashWorker.managed_cmd_group)
            and self.cm_attr_managed_updated is False
            and self.cm_attr_parsed_json_updated is True
        ):
            self._update_cm_attr_managed()
        if all(
            worker.is_finished
            for worker in self.workers
            if worker.group == SplashWorker.splash_cmd_group
            or worker.group == SplashWorker.cm_attr_group
            or worker.group == SplashWorker.managed_cmd_group
        ):
            self.dismiss()
