from collections import deque
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.geometry import Region
from textual.screen import Screen
from textual.strip import Strip
from textual.timer import Timer
from textual.widgets import RichLog, Static
from textual.worker import WorkerState

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.id_typing import LogTabEntry, SplashIdStr

SPLASH = """\
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
""".replace(
    "===", "=\u200b=\u200b="
).splitlines()


def create_deque() -> deque[Style]:
    start_color = "#0178D4"
    end_color = "#F187FB"

    fade = [start_color] * 8
    gradient = Gradient.from_colors(start_color, end_color, quality=6)
    fade.extend([color.hex for color in gradient.colors])
    gradient.colors.reverse()
    fade.extend([color.hex for color in gradient.colors])

    line_styles = deque([Style(color=color, bold=True) for color in fade])
    return line_styles


LINE_STYLES = create_deque()
LINE_STYLES.rotate(-2)
SPLASH_HEIGHT = len(SPLASH)
SPLASH_WIDTH = len(max(SPLASH, key=len))

LOG_PADDING_WIDTH = 36
LONG_COMMANDS = chezmoi.long_commands

RICH_LOG = RichLog(id=SplashIdStr.splash_rich_log_id)
RICH_LOG.styles.height = len(LONG_COMMANDS) + 2
RICH_LOG.styles.width = LOG_PADDING_WIDTH + 9
RICH_LOG.styles.color = "#0053AA"
RICH_LOG.styles.margin = 0
RICH_LOG.styles.padding = 0

COMMAND_LOG: list[LogTabEntry] = []


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__(id=SplashIdStr.animated_fade_id)
        self.styles.height = SPLASH_HEIGHT
        self.styles.width = SPLASH_WIDTH
        self.styles.margin = 1

    def render_lines(self, crop: Region) -> list[Strip]:
        LINE_STYLES.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=LINE_STYLES[y])])


class LoadingScreen(Screen[list[LogTabEntry]]):

    def __init__(self) -> None:
        super().__init__(id=SplashIdStr.loading_screen_id)
        # Timers will be set in on_mount()
        self.fade_timer: Timer
        self.all_workers_timer: Timer
        self.temp_config_timer: Timer

    def compose(self) -> ComposeResult:
        yield Middle(Center(AnimatedFade()), Center(RICH_LOG))

    def log_text(self, log_label: str) -> None:
        padding = LOG_PADDING_WIDTH - len(log_label)
        log_text = f"{log_label} {'.' * padding} loaded"

        def update_log():
            RICH_LOG.write(log_text)

        self.app.call_from_thread(update_log)

    def run_command(self, attr: str) -> None:
        io_class = getattr(chezmoi, attr)
        io_class.update()
        self.log_text(io_class.label)
        long_command = getattr(chezmoi, attr).long_command
        COMMAND_LOG.append(
            LogTabEntry(
                long_command=long_command,
                message="output stored in InputOutput by 'splash.py'.",
            )
        )

    @work(thread=True, group="io_workers")
    def run_io_worker(self, arg_id: str) -> None:
        self.run_command(arg_id)

    @work(thread=True, group="doctor")
    def run_doctor_worker(self) -> None:
        self.run_command("doctor")

    @work(thread=True, group="cat_config")
    def run_cat_config_worker(self) -> None:
        self.run_command("cat_config")

    @work(thread=True, group="set_temp_config_file")
    def set_temp_config_file(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.app.workers
            if worker.group in ("doctor", "cat_config")
        ):
            if chezmoi.check_interactive():
                self.temp_config_timer.stop()
                temp_config_path: Path | None = (
                    chezmoi.create_temp_config_file()
                )

                from chezmoi_mousse.chezmoi import PerformChange

                PerformChange.config_path = temp_config_path

                self.log_text("create non interactive config")

                COMMAND_LOG.append(
                    LogTabEntry(
                        ("Create non_interactive config",),
                        message=f"Create temporary config file at {temp_config_path} excluding interactive option.",
                    )
                )

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.app.workers
            if worker.group
            in ("io_workers", "doctor", "cat_config", "set_temp_config_file")
        ):
            result: list[LogTabEntry] = COMMAND_LOG
            self.dismiss(result)

    def on_mount(self) -> None:
        animated_fade = self.query_exactly_one(AnimatedFade)
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )
        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.temp_config_timer = self.set_interval(
            interval=0.1, callback=self.set_temp_config_file
        )

        # first run chezzmoi doctor, most expensive command
        self.run_doctor_worker()
        # run cat config so the temp config file can be created
        LONG_COMMANDS.pop("doctor")
        self.run_cat_config_worker()
        LONG_COMMANDS.pop("cat_config")

        for arg_id in LONG_COMMANDS:
            self.run_io_worker(arg_id)
