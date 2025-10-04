from collections import deque
from dataclasses import fields
from threading import Lock
from time import sleep

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

# from chezmoi_mousse.chezmoi import ReadCmd, VerbArgs
from chezmoi_mousse.custom_theme import vars as theme_vars
from chezmoi_mousse.id_typing import AppType, SplashReturnData
from chezmoi_mousse.id_typing.enums import ReadCmd, VerbArgs
from chezmoi_mousse.logs_tab import AppLog

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

LOG_PADDING_WIDTH = 41


class SplashLog(RichLog, AppType):
    def __init__(self) -> None:
        super().__init__()
        self.styles.width = LOG_PADDING_WIDTH + 9
        self.styles.color = "#6DB2FF"
        self.styles.margin = 1
        self.styles.padding = 0


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()
        self.line_styles = self.create_deque()
        self.line_styles.rotate(-3)
        self.styles.height = len(SPLASH)
        self.styles.width = len(max(SPLASH, key=len))
        self.styles.margin = 1

    def render_lines(self, crop: Region) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

    def create_deque(self) -> deque[Style]:
        start_color = "#0178D4"
        end_color = "#F187FB"

        fade = [start_color] * 8
        gradient = Gradient.from_colors(start_color, end_color, quality=6)
        fade.extend([color.hex for color in gradient.colors])
        gradient.colors.reverse()
        fade.extend([color.hex for color in gradient.colors])

        line_styles = deque([Style(color=color, bold=True) for color in fade])
        return line_styles


class LoadingScreen(Screen[SplashReturnData], AppType):

    def __init__(self) -> None:
        self.splash_return_data = SplashReturnData(
            doctor="",
            dir_status_lines="",
            file_status_lines="",
            managed_dirs="",
            managed_files="",
        )
        self.data_lock = Lock()  # Add thread lock
        self.rich_log = SplashLog()
        super().__init__()

        # TODO add logic so screen does not get dismissed in the "middle" of a
        # fade, looks better
        self.fade_timer: Timer
        self.all_workers_timer: Timer

    def compose(self) -> ComposeResult:
        yield Middle(Center(AnimatedFade()), Center(self.rich_log))

    def update_and_log(self, field_name: str, cmd_output: str) -> None:
        command_value = getattr(ReadCmd, field_name).value
        cmd_text = "cmd from splash screen"
        cmd_text = (
            AppLog.pretty_cmd_str(command_value)
            .replace(VerbArgs.include_dirs.value, "dirs")
            .replace(VerbArgs.include_files.value, "files")
        )
        padding = LOG_PADDING_WIDTH - len(cmd_text)
        log_text = f"{cmd_text} {'.' * padding} loaded"

        def update_log():
            self.rich_log.write(log_text)

        def update_data():
            with self.data_lock:  # Thread-safe update
                setattr(self.splash_return_data, field_name, cmd_output)

        self.app.call_from_thread(update_log)
        update_data()  # Call directly since it's now thread-safe

    @work(thread=True, group="io_workers")
    def log_unavailable_chezmoi_command(self) -> None:
        message = "chezmoi command ................. not found"
        color = theme_vars["text-primary"]
        self.rich_log.styles.margin = 1
        self.rich_log.markup = True
        self.rich_log.styles.width = len(message) + 2
        self.rich_log.write(f"[{color}]{message}[/]")
        sleep(0.5)

    @work(thread=True, group="io_workers")
    def run_read_cmd(self, field_name: str) -> None:

        command_to_run = getattr(ReadCmd, field_name)
        cmd_output = self.app.chezmoi.read(command_to_run)

        self.update_and_log(field_name, cmd_output)

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.workers
            if worker.group == "io_workers"
        ):
            self.dismiss(self.splash_return_data)

    def on_mount(self) -> None:

        animated_fade = self.query_exactly_one(AnimatedFade)
        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )

        if not self.app.chezmoi.chezmoi_found:
            self.log_unavailable_chezmoi_command()
            return

        field_names = [field.name for field in fields(SplashReturnData)]
        self.rich_log.styles.height = len(field_names) + 2
        for field_name in field_names:
            self.run_read_cmd(field_name)
