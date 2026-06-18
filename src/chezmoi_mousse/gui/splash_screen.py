import json
from collections import deque
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual import events, work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.geometry import Region
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static
from textual.worker import WorkerState

from chezmoi_mousse import CMD, ReadCmd

__all__ = ["SplashScreen"]


SPLASH_COMMANDS: list[ReadCmd] = [
    ReadCmd.cat_config,
    ReadCmd.doctor,
    ReadCmd.dump_config,
    ReadCmd.git_log,
    ReadCmd.ignored,
    ReadCmd.managed_dirs,
    ReadCmd.managed_files,
    ReadCmd.status_dirs,
    ReadCmd.status_files,
    ReadCmd.template_data,
]

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
        self.styles.height = len(SPLASH_COMMANDS) + 1  # +1 for parse dump-config log
        self.styles.width = "auto"
        self.styles.margin = 2
        self.markup = True


class SplashScreen(Screen[None]):

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
        for splash_cmd in SPLASH_COMMANDS:
            self._run_io_worker(splash_cmd)

    @work(thread=True, group="io_workers")
    def _run_io_worker(self, splash_cmd: ReadCmd) -> None:
        color = self.app.theme_variables["text-primary"]
        result = CMD.run_cmd.read(splash_cmd)
        setattr(CMD.cache.cmd_results, f"{splash_cmd.name}", result)
        suffix = "unknown"
        if result.exit_code == 0:
            suffix = "success"
        else:
            suffix = "checked"
            color = self.app.theme_variables["text-warning"]
        padding = LOG_MSG_WIDTH - (len(result.short_cmd_no_path) + len(suffix))
        log_text = (
            f"[{color}]{result.short_cmd_no_path} {'.' * padding} {suffix}[/{color}]"
        )
        self.app.call_from_thread(self.splash_log.write, log_text)
        if splash_cmd == ReadCmd.dump_config:
            try:
                parsed_cfg = json.loads(result.std_out)
                CMD.cache.dest_dir = Path(parsed_cfg["destDir"])
                CMD.cache.git_auto_commit = parsed_cfg["git"]["autocommit"]
                CMD.cache.git_auto_push = parsed_cfg["git"]["autopush"]
                color = self.app.theme_variables["text-success"]
                suffix = "success"
            except (json.JSONDecodeError, KeyError, TypeError):
                color = self.app.theme_variables["text-error"]
                suffix = "not parsed"
            command = "json loads dump_config"
            padding = LOG_MSG_WIDTH - (len(command) + len(suffix))
            log_text = f"[{color}]{command} {'.' * padding} {suffix}[/{color}]"
            self.app.call_from_thread(self.splash_log.write, log_text)

    def _all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.workers
            if worker.group == "io_workers"
        ):
            if CMD.run_cmd.chezmoi_bin is None:
                self.dismiss(None)
                return
            CMD.cache.update_path_sets()
            if all(w for w in self.workers if w.is_finished):
                self.dismiss()
