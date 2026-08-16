from __future__ import annotations

import asyncio
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
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse.cm_attributes import ManagedPaths, ResultCollector
from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.named_tuples import CommandResult
from chezmoi_mousse.str_enums import ColorVar

from .common.ascii_constants import SPLASH_ASCII

if TYPE_CHECKING:
    from chezmoi_mousse.gui.textual_app import ChezmoiGui

__all__ = ["SplashScreen"]


SPLASH_WIDTH = len(max(SPLASH_ASCII, key=len))
LOG_MSG_WIDTH = SPLASH_WIDTH - 13


def create_fade_line_styles() -> deque[Style]:
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


FADE_LINE_STYLES: deque[Style] = create_fade_line_styles()


class GroupName(StrEnum):
    json_output_group = auto()
    managed_cmd_group = auto()
    splash_cmd_group = auto()


class WorkerName(StrEnum):
    parse_json_outputs = "parse json outputs"
    update_managed_paths = "update managed paths"
    set_cm_attributes = "set cmattr"


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
        self.splash_log.styles.text_align = "center"
        self.splash_log.styles.margin = 2
        self.splash_log.styles.height = (
            self.app.cmattr.read_cmd_groups.commands_count + 3
        )

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
        result: CommandResult = Commands.run_read_cmd(command)
        return self._get_log_msg(prefix=result.pretty_cmd, returncode=result.returncode)

    # Threaded Command Workers

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

    # Non-threaded Workers for tasks that are not worth creating a thread for

    @work(name=WorkerName.update_managed_paths)
    async def _create_managed_paths_instance(self) -> None:
        ResultCollector.managed_paths_instance = ManagedPaths(
            _dest_dir=Path(ResultCollector.parsed_dump_config["destDir"]),
            _managed_dirs_result=ResultCollector.managed_dirs,
            _managed_files_result=ResultCollector.managed_files,
            _status_dirs_result=ResultCollector.status_dirs,
            _status_files_result=ResultCollector.status_files,
        )
        msg = self._get_log_msg(prefix=WorkerName.update_managed_paths, returncode=None)
        self.splash_log.write(msg)

    @work(name=WorkerName.parse_json_outputs)
    async def _parse_json_outputs(self) -> None:
        parsed_dump_config = Commands.json_loads(ResultCollector.dump_config.std_out)
        parsed_template_data = Commands.json_loads(
            ResultCollector.template_data.std_out
        )
        ResultCollector.parsed_dump_config = parsed_dump_config
        ResultCollector.parsed_template_data = parsed_template_data
        msg = self._get_log_msg(prefix=WorkerName.parse_json_outputs, returncode=None)
        self.splash_log.write(msg)

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
        msg = self._get_log_msg(prefix=WorkerName.set_cm_attributes, returncode=None)
        self.splash_log.write(msg)

    # Sequential Orchestration Pipeline

    @work
    async def _run_all_tasks(self) -> None:
        self.fade_timer.resume()

        # Dispatch command workers and store worker instances for awaiting later.
        json_workers = [
            self._run_json_output_cmd(cmd)
            for cmd in self.app.cmattr.read_cmd_groups.json_output
        ]
        managed_workers = [
            self._run_managed_cmd(cmd)
            for cmd in self.app.cmattr.read_cmd_groups.managed
        ]
        splash_workers = [
            self._run_splash_cmd(cmd)
            for cmd in self.app.cmattr.read_cmd_groups.splash_only
        ]

        # Await JSON output read commands and then parse them.
        for worker in json_workers:
            await worker.wait()
        await self._parse_json_outputs().wait()

        # Await Managed paths read commands and then create the cmattr.paths instance.
        for worker in managed_workers:
            await worker.wait()
        await self._create_managed_paths_instance().wait()

        # Wait for remaining splash commands, if any, before setting all cm attributes.
        for worker in splash_workers:
            await worker.wait()
        await self._set_cm_attributes().wait()

        # Only dismiss after a completed fade cycle
        while (
            self.animated_fade.step_count < 20
            or self.animated_fade.step_count % 20 != 0
        ):
            await asyncio.sleep(0.05)

        self.dismiss()
