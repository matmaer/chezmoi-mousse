from __future__ import annotations

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
from chezmoi_mousse.cm_types import CmdResultCollector, ManagedResults, SplashResults
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


class GroupNames(StrEnum):
    json_output_group = auto()
    managed_cmd_group = auto()
    splash_cmd_group = auto()


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
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.width = "auto"
        self.splash_log.styles.text_align = "center"
        self.splash_log.styles.margin = 2
        self.splash_log.styles.height = (
            self.app.cm_attr.read_cmd_groups.commands_count + 2
        )
        fade_timer = self.query_exactly_one(AnimatedFade).fade_timer
        self.primary_color = self.app.theme_variables["text-primary"]
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

    def _get_log_msg(self, *, prefix: str, suffix: str, returncode: int | None) -> str:
        padding = LOG_MSG_WIDTH - (len(prefix) + len(suffix))
        color = (
            self.primary_color
            if returncode == 0 or returncode is None
            else self.warning_color
        )
        return f"[{color}]{prefix} {'.' * padding} {suffix}[/{color}]"

    def _run_chezmoi_command(self, command: ReadCmd) -> str:
        result: CommandResult = run_chezmoi_cmd(command, dry_run=False)
        setattr(CmdResultCollector, command.name, result)
        suffix = "completed"
        if command in self.app.cm_attr.read_cmd_groups.json_output:
            suffix = "completed and parsed"
            if command == ReadCmd.dump_config and result.parsed_json is not None:
                self.app.cm_attr.parsed_config_dump = result.parsed_json
                CmdResultCollector.dest_dir = Path(result.parsed_json["destDir"])
            elif command == ReadCmd.template_data and result.parsed_json is not None:
                self.app.cm_attr.parsed_template_data = result.parsed_json
        return self._get_log_msg(
            prefix=result.pretty_cmd, suffix=suffix, returncode=result.returncode
        )

    # Command groups

    @work(thread=True, group=GroupNames.splash_cmd_group)
    def _run_splash_cmd(self, command: ReadCmd) -> None:
        msg = self._run_chezmoi_command(command)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group=GroupNames.managed_cmd_group)
    def _run_managed_cmd(self, command: ReadCmd) -> None:
        msg = self._run_chezmoi_command(command)
        self.app.call_from_thread(self.splash_log.write, msg)

    @work(thread=True, group=GroupNames.json_output_group)
    def _run_json_output_cmd(self, command: ReadCmd) -> None:
        msg = self._run_chezmoi_command(command)
        self.app.call_from_thread(self.splash_log.write, msg)

    # set update ManagedPaths which accessed through cm_attr.paths

    @work(thread=True)
    def _update_managed_paths(self, managed_results: ManagedResults) -> None:

        self.app.cm_attr.update_paths(results=managed_results)
        self.cm_attr_managed_updated = True
        msg = self._get_log_msg(
            prefix="update paths", suffix="completed", returncode=None
        )
        self.app.call_from_thread(self.splash_log.write, msg)

    def _all_workers_finished(self) -> None:
        if not all(
            worker.is_finished
            for worker in self.workers
            if worker.group == GroupNames.json_output_group
            or worker.group == GroupNames.managed_cmd_group
        ):
            return
        else:
            managed_results: ManagedResults = CmdResultCollector.get_managed_results()
            self._update_managed_paths(
                dest_dir=CmdResultCollector.dest_dir, managed_results=managed_results
            )
        if all(worker.is_finished for worker in self.workers) and all(
            worker.is_finished for worker in self.app.workers
        ):
            self.dismiss(CmdResultCollector.get_all_results())
