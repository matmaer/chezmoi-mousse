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

from chezmoi_mousse.cm_attributes import ManagedPaths
from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.cm_types import ManagedResults, ResultCollector
from chezmoi_mousse.functions import Commands

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import CommandResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

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
    set_cm_attributes = "set cmattr"


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
            yield Center(RichLog(markup=True))

    def on_mount(self) -> None:
        self.json_output_parsed = False
        self.managed_paths_instance_ready = False
        self.cm_attributes_set = False
        self.splash_log = self.query_exactly_one(RichLog)
        self.splash_log.styles.width = "auto"
        self.splash_log.styles.text_align = "center"
        self.splash_log.styles.margin = 2
        self.splash_log.styles.height = (
            self.app.cmattr.read_cmd_groups.commands_count + 2
        )
        fade_timer = self.query_exactly_one(AnimatedFade).fade_timer
        self.primary_color = self.app.theme_variables["text-primary"]
        self.success_color = self.app.theme_variables["text-success"]
        self.warning_color = self.app.theme_variables["text-warning"]
        self.error_color = self.app.theme_variables["text-error"]
        for command in self.app.cmattr.read_cmd_groups.json_output:
            self._run_json_output_cmd(command)
        for command in self.app.cmattr.read_cmd_groups.managed:
            self._run_managed_cmd(command)
        for command in self.app.cmattr.read_cmd_groups.splash_only:
            self._run_splash_cmd(command)
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
        result: CommandResult = Commands.run_read_cmd(command)
        setattr(ResultCollector, command.name, result)
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

    @work(name=WorkerName.parse_json_output)
    async def _parse_json_outputs(self) -> None:
        parsed_dump_config = Commands.json_loads(ResultCollector.dump_config.std_out)
        parsed_template_data = Commands.json_loads(
            ResultCollector.template_data.std_out
        )
        ResultCollector.parsed_dump_config = parsed_dump_config
        ResultCollector.parsed_template_data = parsed_template_data
        ResultCollector.dest_dir = parsed_dump_config["destDir"]
        self.json_output_parsed = True

    @work(name=WorkerName.set_cm_attributes)
    async def _set_cm_attributes(self) -> None:
        self.app.cmattr.dest_dir = Path(ResultCollector.parsed_dump_config["destDir"])
        self.app.cmattr.auto_add = ResultCollector.parsed_dump_config["git"]["autoadd"]
        self.app.cmattr.auto_commit = ResultCollector.parsed_dump_config["git"][
            "autocommit"
        ]
        self.app.cmattr.auto_push = ResultCollector.parsed_dump_config["git"][
            "autopush"
        ]
        self.app.cmattr.cmd_results = ResultCollector()
        self.app.cmattr.paths = ResultCollector.managed_paths_instance
        self.cm_attributes_set = True
        msg = self._get_log_msg(prefix=WorkerName.set_cm_attributes, returncode=None)
        self.splash_log.write(msg)

    def _all_workers_finished(self) -> None:
        if self.json_output_parsed is False and all(
            worker.is_finished
            for worker in self.workers
            if worker.group == GroupName.json_output_group
        ):
            _ = self._parse_json_outputs().wait()  # WorkerName.parse_json_output
            msg = self._get_log_msg(
                prefix=WorkerName.parse_json_output, returncode=None
            )
            self.splash_log.write(msg)
            return
        elif (
            self.json_output_parsed is True
            and self.managed_paths_instance_ready is False
            and all(
                worker.is_finished
                for worker in self.workers
                if worker.group == GroupName.managed_cmd_group
            )
        ):
            ResultCollector.managed_paths_instance = ManagedPaths(
                results=ManagedResults(
                    dest_dir=ResultCollector.dest_dir,
                    managed_dirs=ResultCollector.managed_dirs,
                    managed_files=ResultCollector.managed_files,
                    status_dirs=ResultCollector.status_dirs,
                    status_files=ResultCollector.status_files,
                )
            )
            msg = self._get_log_msg(prefix=WorkerName.update_paths, returncode=None)
            self.splash_log.write(msg)
            self.managed_paths_instance_ready = True
            return

        if (
            self.json_output_parsed is True
            and self.managed_paths_instance_ready is True
            and all(worker.is_finished for worker in self.workers)
        ):
            _ = self._set_cm_attributes().wait()  # WorkerName.set_cm_attributes
            self.dismiss()
