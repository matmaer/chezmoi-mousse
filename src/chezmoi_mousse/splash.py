"""Initialize all data in the InputOutput dataclasses for chezmoi.py."""

from collections import deque
from pathlib import Path

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


start_color = "#0178D4"
end_color = "#F187FB"
fade = [start_color] * 7
gradient = Gradient.from_colors(start_color, end_color, quality=4)
fade.extend([color.hex for color in gradient.colors])
gradient.colors.reverse()
fade.extend([color.hex for color in gradient.colors])
line_styles = deque([Style(color=color, bold=True) for color in fade])
fade_height = len(SPLASH)
fade_width = len(max(SPLASH, key=len)) - 2

DEST_DIR: Path
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
        self.styles.height = fade_height
        self.styles.width = fade_width
        self.styles.margin = 2

    def render_lines(self, crop) -> list[Strip]:
        line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.1, callback=self.refresh)


ANIMATED_FADE = AnimatedFade()


class LoadingScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Middle(Center(ANIMATED_FADE), Center(RICH_LOG))

    def log_text(self, log_label: str) -> None:
        padding = LOG_PADDING_WIDTH - len(log_label)

        def update_log():
            log_text = f"{log_label} {'.' * padding} loaded"
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
        # first run chezzmoi doctor as it is the most expensive command so the
        # other threads can run while it's being executed
        self.run_io_worker("doctor")
        LONG_COMMANDS.pop("doctor")
        # the doctor command has been removed from LONG_COMMANDS
        for arg_id in LONG_COMMANDS:
            self.run_io_worker(arg_id)
        self.set_interval(interval=1.2, callback=self.all_workers_finished)
