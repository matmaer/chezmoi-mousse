"""Initialize all data in the InputOutput dataclasses for chezmoi.py."""

from collections import deque

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse.chezmoi import chezmoi

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

RICH_LOG = RichLog(id="loading_screen_log")
RICH_LOG.styles.height = len(LONG_COMMANDS)
RICH_LOG.styles.width = LOG_PADDING_WIDTH + 9
RICH_LOG.styles.color = "#0053AA"
RICH_LOG.styles.margin = 0
RICH_LOG.styles.padding = 0

COMMAND_LOG: list[tuple[list, str]] = []


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = SPLASH_HEIGHT
        self.styles.width = SPLASH_WIDTH
        self.styles.margin = 1

    def render_lines(self, crop) -> list[Strip]:
        LINE_STYLES.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=LINE_STYLES[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.05, callback=self.refresh)


class LoadingScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Middle(Center(AnimatedFade()), Center(RICH_LOG))

    def log_text(self, log_label: str) -> None:
        padding = LOG_PADDING_WIDTH - len(log_label)
        log_text = f"{log_label} {'.' * padding} loaded"

        def update_log():
            RICH_LOG.write(log_text)

        self.app.call_from_thread(update_log)

    @work(thread=True, group="io_workers")
    def run_io_worker(self, arg_id) -> None:
        io_class = getattr(chezmoi, arg_id)
        io_class.update()
        self.log_text(io_class.label)
        long_command = getattr(chezmoi, arg_id).long_command
        COMMAND_LOG.append(
            (
                long_command,
                "output stored in an InputOutput dataclass by 'splash.py'.",
            )
        )

    def all_workers_finished(self) -> None:
        if all(
            worker.state == "finished"
            for worker in self.app.workers
            if worker.group == "io_workers"
        ):
            self.dismiss(COMMAND_LOG)

    def on_mount(self) -> None:
        # first run chezzmoi doctor, most expensive command
        self.run_io_worker("doctor")
        LONG_COMMANDS.pop("doctor")
        for arg_id in LONG_COMMANDS:
            self.run_io_worker(arg_id)
        self.set_interval(interval=1, callback=self.all_workers_finished)
