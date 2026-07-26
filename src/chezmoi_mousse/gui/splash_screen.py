from __future__ import annotations

import json
from collections import deque
from enum import StrEnum, auto
from pathlib import Path
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

from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.cm_types import CmdResultCollector, SplashResults
from chezmoi_mousse.functions import run_chezmoi_cmd

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ChezmoiGui, CommandResult

__all__ = ["SplashScreen"]

SPLASH_ASCII = """\
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
""".replace("===", "=\u200b=\u200b=").splitlines()

SPLASH_WIDTH = len(max(SPLASH_ASCII, key=len))
LOG_MSG_WIDTH = SPLASH_WIDTH - 13


def create_fade_line_styles() -> deque[Style]:
    start_color = "#0178D4"
    end_color = "#F187FB"
    fade = [start_color] * 8
    gradient = Gradient.from_colors(start_color, end_color, quality=6)
    fade.extend([color.hex for color in gradient.colors])
    gradient.colors.reverse()
    fade.extend([color.hex for color in gradient.colors])
    fade_line_styles = deque(
        [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
    )
    fade_line_styles.rotate(-2)
    return fade_line_styles


FADE_LINE_STYLES: deque[Style] = create_fade_line_styles()


class GroupName(StrEnum):
    json_output_group = auto()
    managed_cmd_group = auto()
    splash_cmd_group = auto()


class WorkerName(StrEnum):
    parse_json_output = "parse json output"
    update_paths = "update paths"


class AnimatedFade(Static):

    def on_mount(self) -> None:
        self.styles.height = len(SPLASH_ASCII)
        self.styles.width = SPLASH_WIDTH
        self.fade_timer = self.set_interval(
            name="refresh_self", interval=0.1, callback=self.refresh, pause=True
        )

    def render_lines(self, crop: Region) -> list[Strip]:
        FADE_LINE_STYLES.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH_ASCII[y], style=FADE_LINE_STYLES[y])])


class SplashScreen(Screen[SplashResults]):

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
            yield Center(RichLog(markup=True))

    def on_mount(self) -> None:
        self.json_output_parsed = False
        self.managed_paths_updated = False
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.width = "auto"
        self.splash_log.styles.text_align = "center"
        self.splash_log.styles.margin = 2
        self.splash_log.styles.height = (
            self.app.cm_attr.read_cmd_groups.commands_count + 2
        )
        fade_timer = self.query_exactly_one(AnimatedFade).fade_timer
        self.primary_color = self.app.theme_variables["text-primary"]
        self.success_color = self.app.theme_variables["text-success"]
        self.warning_color = self.app.theme_variables["text-warning"]
        self.error_color = self.app.theme_variables["text-error"]
        for command in self.app.cm_attr.read_cmd_groups.managed:
            self._run_managed_cmd(command)
        for command in self.app.cm_attr.read_cmd_groups.splash_only:
            self._run_splash_cmd(command)
        for command in self.app.cm_attr.read_cmd_groups.json_output:
            self._run_json_output_cmd(command)
        self.set_interval(interval=2, callback=self._all_workers_finished)
        fade_timer.resume()

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
        result: CommandResult = run_chezmoi_cmd(command, dry_run=False)
        setattr(CmdResultCollector, command.name, result)
        return self._get_log_msg(prefix=result.pretty_cmd, returncode=result.returncode)

    # Command groups

    @work(thread=True, group=GroupName.splash_cmd_group)
    def _run_splash_cmd(self, command: ReadCmd) -> None:
        msg = self._run_chezmoi_command(command)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group=GroupName.managed_cmd_group)
    def _run_managed_cmd(self, command: ReadCmd) -> None:
        msg = self._run_chezmoi_command(command)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group=GroupName.json_output_group)
    def _run_json_output_cmd(self, command: ReadCmd) -> None:
        msg = self._run_chezmoi_command(command)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, name=WorkerName.parse_json_output)
    def parse_json_outputs(self) -> None:
        parsed_dump_config = json.loads(CmdResultCollector.dump_config.std_out)
        parsed_template_data = json.loads(CmdResultCollector.template_data.std_out)
        CmdResultCollector.parsed_dump_config = parsed_dump_config
        CmdResultCollector.parsed_template_data = parsed_template_data
        CmdResultCollector.dest_dir = parsed_dump_config["destDir"]
        self.app.cm_attr.dest_dir = Path(parsed_dump_config["destDir"])
        self.app.cm_attr.auto_add = parsed_dump_config["git"]["autoadd"]
        self.app.cm_attr.auto_commit = parsed_dump_config["git"]["autocommit"]
        self.app.cm_attr.auto_push = parsed_dump_config["git"]["autopush"]
        self.json_output_parsed = True
        msg = self._get_log_msg(prefix=WorkerName.parse_json_output, returncode=None)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, name=WorkerName.update_paths)
    def _update_managed_paths(self) -> None:
        managed_results = CmdResultCollector.get_managed_results()
        self.app.cm_attr.update_paths(results=managed_results)
        msg = self._get_log_msg(prefix="update paths", returncode=None)
        self.managed_paths_updated = True
        self.app.call_from_thread(self.splash_log.write, msg)

    def _all_workers_finished(self) -> None:
        if self.json_output_parsed is False and all(
            worker.is_finished
            for worker in self.workers
            if worker.group == GroupName.json_output_group
        ):
            self.parse_json_outputs()  # WorkerName.parse_json_output
            return
        if (
            self.managed_paths_updated is False
            and all(
                worker.is_finished
                for worker in self.workers
                if worker.name == WorkerName.parse_json_output
            )
            and all(
                worker.is_finished
                for worker in self.workers
                if worker.group == GroupName.managed_cmd_group
            )
        ):
            self._update_managed_paths()  # WorkerName.update_paths
            return
        if all(worker.is_finished for worker in self.app.workers):
            self.app.cm_attr.splash_results = CmdResultCollector.get_splash_results()
            self.app.cm_attr.parsed_dump_config = CmdResultCollector.parsed_dump_config
            self.app.cm_attr.parsed_template_data = (
                CmdResultCollector.parsed_template_data
            )
            self.dismiss()
