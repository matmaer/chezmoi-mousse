from collections import deque
from dataclasses import fields

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

FADE_HEIGHT = len(SPLASH)
FADE_WIDTH = len(max(SPLASH, key=len))
LOG_PADDING_WIDTH = 37


def create_deque() -> deque[Style]:
    start_color = "#0178D4"
    end_color = "#F187FB"

    fade = [start_color] * 12
    gradient = Gradient.from_colors(start_color, end_color, quality=6)
    fade.extend([color.hex for color in gradient.colors])
    gradient.colors.reverse()
    fade.extend([color.hex for color in gradient.colors])

    line_styles = deque(
        [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
    )
    return line_styles


FADE_LINE_STYLES = create_deque()
cat_config: str = ""
doctor: str = ""
dump_config: str = ""
ignored: str = ""
managed_dirs: str = ""
managed_files: str = ""
status_dirs: str = ""
status_files: str = ""
template_data: str = ""


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = FADE_HEIGHT
        self.styles.width = FADE_WIDTH
        self.styles.margin = 2

    def render_lines(self, crop: Region) -> list[Strip]:
        FADE_LINE_STYLES.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=FADE_LINE_STYLES[y])])


class LoadingScreen(Screen[SplashReturnData | None], AppType):

    def __init__(self, chezmoi_found: bool) -> None:
        self.chezmoi_found = chezmoi_found
        self.fade_timer: Timer
        self.all_workers_timer: Timer
        super().__init__()

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog())

    @work(thread=True, group="io_workers")
    def run_read_cmd(self, field_name: str) -> None:

        splash_log = self.query_exactly_one(RichLog)

        if not self.chezmoi_found:
            cmd_text = "chezmoi command"
            self.log_text_suffix = "not found"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            log_text = f"{cmd_text} {'.' * padding} not found"
            splash_log.write(log_text)
            return

        cmd_output = self.app.chezmoi.read(getattr(ReadCmd, field_name))
        globals()[field_name] = cmd_output
        command_value = getattr(ReadCmd, field_name).value
        cmd_text = (
            LogUtils.pretty_cmd_str(command_value)
            .replace(VerbArgs.include_dirs.value, "dirs")
            .replace(VerbArgs.include_files.value, "files")
        )
        padding = LOG_PADDING_WIDTH - len(cmd_text)
        log_text = f"{cmd_text} {'.' * padding} loaded"
        splash_log.write(log_text)

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "io_workers"
        ):
            if self.chezmoi_found is False:
                self.dismiss(None)
                return

            self.dismiss(
                SplashReturnData(
                    cat_config=globals()["cat_config"],
                    doctor=globals()["doctor"],
                    dump_config=globals()["dump_config"],
                    ignored=globals()["ignored"],
                    managed_dirs=globals()["managed_dirs"],
                    managed_files=globals()["managed_files"],
                    status_dirs=globals()["status_dirs"],
                    status_files=globals()["status_files"],
                    status_paths=globals()["status_paths"],
                    template_data=globals()["template_data"],
                )
            )

    def on_mount(self) -> None:
        animated_fade = self.query_exactly_one(AnimatedFade)
        rich_log = self.query_exactly_one(RichLog)
        rich_log.styles.color = "#6DB2FF"
        rich_log.styles.width = "auto"
        if self.chezmoi_found:
            rich_log.styles.height = len(fields(SplashReturnData))
        else:
            rich_log.styles.height = 1

        if not self.chezmoi_found:
            self.run_read_cmd("")
        else:
            for field_name in [
                field.name for field in fields(SplashReturnData)
            ]:
                self.run_read_cmd(field_name)

        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )
