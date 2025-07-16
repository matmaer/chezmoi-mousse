import tempfile
from collections import deque
from enum import StrEnum, auto
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

from chezmoi_mousse.chezmoi import ChangeCommand, chezmoi, cmd_log

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


# added to make the logic in test_no_hardcoded_ids pass for splash.py
class SplashIdStr(StrEnum):
    animated_fade_id = auto()
    loading_screen_id = auto()
    splash_rich_log_id = auto()


def modify_config_non_interactive(list_of_strings: list[str]) -> list[str]:
    result: list[str] = []

    replacements = [
        ("true", "false"),
        ("on", "off"),
        ("1", "0"),
        ("yes", "no"),
    ]

    for line in list_of_strings:
        if "interactive" in line.lower():
            for old, new in replacements:
                line = line.replace(old, new)
            result.append(line)
        else:
            result.append(line)
    return result


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
LINE_STYLES.rotate(-3)
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


ANIMATED_FADE = AnimatedFade()
LOADING_SCREEN_COMPOSE = Middle(Center(ANIMATED_FADE), Center(RICH_LOG))


class LoadingScreen(Screen[list[str]]):

    def __init__(self) -> None:
        super().__init__(id=SplashIdStr.loading_screen_id)
        # Timers will be set in on_mount()
        self.fade_timer: Timer
        self.all_workers_timer: Timer

    def compose(self) -> ComposeResult:
        yield LOADING_SCREEN_COMPOSE

    def log_text(self, log_label: str) -> None:
        padding = LOG_PADDING_WIDTH - len(log_label)
        log_text = f"{log_label} {'.' * padding} loaded"

        def update_log():
            RICH_LOG.write(log_text)

        self.app.call_from_thread(update_log)

    @work(thread=True, group="io_workers")
    def run_io_worker(self, arg_id: str) -> None:
        io_class = getattr(chezmoi, arg_id)
        io_class.update()
        self.log_text(io_class.label)

    @work(thread=True, group="doctor")
    def run_doctor_worker(self) -> None:
        config_file_path: Path | None = None
        io_class = getattr(chezmoi, "doctor")
        io_class.update()
        self.log_text(io_class.label)
        # get config file name from doctor output to run self.set_temp_config_file
        for line in io_class.list_out:
            # Example line: "ok config-file found ~/.config/chezmoi/chezmoi.toml, last modified ..."
            if "config-file" in line and "found" in line:
                parts = line.split("found ")
                if len(parts) > 1:
                    config_file_path = Path(parts[1].split(",")[0].strip())
                    break
        else:
            raise RuntimeError(
                "No config file found in chezmoi doctor output."
            )
        cmd_log.log_success(
            f"found config file {config_file_path} in doctor output"
        )
        self.set_temp_config_file(config_file_path)

    @work(thread=True, group="io_workers")
    def set_temp_config_file(self, config_file_path: Path) -> None:
        # read and create config
        config_lines = chezmoi.run.cat_config()
        self.log_text("chezmoi cat config")

        if not any("interactive" in line.lower() for line in config_lines):
            ChangeCommand.config_path = config_file_path
            cmd_log.log_success(f"Config path set to {config_file_path}.")
            return

        new_config_lines: list[str] = modify_config_non_interactive(
            config_lines
        )
        new_config_str = "\n".join(new_config_lines)

        temp_file_path: Path = (
            Path(tempfile.gettempdir()) / config_file_path.name
        )
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(new_config_str)
        cmd_log.log_success(
            f"created non-interactive config {temp_file_path}, output:"
        )
        cmd_log.log_dimmed(new_config_str)
        ChangeCommand.config_path = temp_file_path
        cmd_log.log_success(f"Config path set to {config_file_path}.")
        self.log_text("Non-interactive config")

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.app.workers
            if worker.group in ("io_workers", "doctor")
        ):
            cmd_log.log_success("--- splash.py finished loading ---")
            self.dismiss()

    def on_mount(self) -> None:
        animated_fade = self.query_exactly_one(AnimatedFade)
        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )

        # first run chezmoi doctor, most expensive command
        self.run_doctor_worker()
        LONG_COMMANDS.pop("doctor")

        for arg_id in LONG_COMMANDS:
            self.run_io_worker(arg_id)
