from collections import deque
from dataclasses import fields
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

from chezmoi_mousse import ReadCmd, VerbArgs
from chezmoi_mousse.gui import AppType, SplashReturnData
from chezmoi_mousse.gui.rich_logs import LogUtils

__all__ = ["LoadingScreen"]


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


class SplashLog(RichLog):
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

        line_styles = deque(
            [
                Style(color=color, bgcolor="#000000", bold=True)
                for color in fade
            ]
        )
        return line_styles


doctor: str = ""
dump_config: str = ""
managed_dirs: str = ""
managed_files: str = ""
status_dirs: str = ""
status_files: str = ""


class LoadingScreen(Screen[SplashReturnData], AppType):

    def __init__(self, chezmoi_found: bool) -> None:
        self.chezmoi_found = chezmoi_found

        super().__init__()

        # TODO add logic so screen does not get dismissed in the "middle" of a
        # fade, looks better
        self.fade_timer: Timer
        self.all_workers_timer: Timer

    def compose(self) -> ComposeResult:
        yield Middle(Center(AnimatedFade()), Center(SplashLog()))

    def update_and_log(self, field_name: str, cmd_output: str) -> None:
        # log_text = "something went wrong"
        if not self.chezmoi_found:
            cmd_text = "chezmoi command"
            self.log_text_suffix = "not found"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            log_text = f"{cmd_text} {'.' * padding} not found"
        else:
            command_value = getattr(ReadCmd, field_name).value
            cmd_text = (
                LogUtils.pretty_cmd_str(command_value)
                .replace(VerbArgs.include_dirs.value, "dirs")
                .replace(VerbArgs.include_files.value, "files")
            )
            padding = LOG_PADDING_WIDTH - len(cmd_text)

            log_text = f"{cmd_text} {'.' * padding} loaded"

        def update_log() -> None:
            splash_log = self.query_exactly_one(SplashLog)
            splash_log.write(log_text)

        self.app.call_from_thread(update_log)

    @work(thread=True, group="io_workers")
    def run_read_cmd(self, field_name: str) -> None:

        command_to_run = getattr(ReadCmd, field_name)
        cmd_output = self.app.chezmoi.read(command_to_run)
        globals()[field_name] = cmd_output

        self.update_and_log(field_name, cmd_output)

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "io_workers"
        ):
            if self.chezmoi_found is False:
                # prevent screen dismissal too quickly
                sleep(0.5)
                self.dismiss(None)
                return

            self.dismiss(
                SplashReturnData(
                    doctor=globals()["doctor"],
                    dump_config=globals()["dump_config"],
                    managed_dirs=globals()["managed_dirs"],
                    managed_files=globals()["managed_files"],
                    status_dirs=globals()["status_dirs"],
                    status_files=globals()["status_files"],
                    status_paths=globals()["status_paths"],
                )
            )

    def on_mount(self) -> None:

        animated_fade = self.query_exactly_one(AnimatedFade)
        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )
        splash_log = self.query_exactly_one(SplashLog)

        if not self.chezmoi_found:
            splash_log.styles.height = 3
            self.update_and_log("", "")
            return

        field_names = [field.name for field in fields(SplashReturnData)]
        splash_log.styles.height = len(field_names) + 2
        for field_name in field_names:
            self.run_read_cmd(field_name)
