from collections import deque
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

from chezmoi_mousse.chezmoi import INIT_CFG
from chezmoi_mousse.constants import SPLASH
from chezmoi_mousse.custom_theme import vars as theme_vars
from chezmoi_mousse.id_typing import AppType, Id

LOG_PADDING_WIDTH = 36


class SplashLog(RichLog, AppType):
    def __init__(self, len_long_cmds: int = 0) -> None:
        super().__init__()

        self.styles.height = len_long_cmds + 2
        self.styles.width = LOG_PADDING_WIDTH + 9
        self.styles.color = "#0057B3"
        self.styles.margin = 0
        self.styles.padding = 0


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__(id=Id.splash_id.animated_fade)
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


class LoadingScreen(Screen[list[str]], AppType):

    def __init__(self) -> None:
        self.long_commands = self.app.chezmoi.io_commands.copy()
        self.rich_log = SplashLog(len_long_cmds=len(self.long_commands))
        super().__init__(id=Id.splash_id.loading_screen)

        # TODO add logic so screen does not get dismissed in the "middle" of a
        # fade, looks better
        self.fade_timer: Timer
        self.all_workers_timer: Timer

    def compose(self) -> ComposeResult:
        yield Middle(Center(AnimatedFade()), Center(self.rich_log))

    def log_text(self, log_label: str) -> None:
        padding = LOG_PADDING_WIDTH - len(log_label)
        log_text = f"{log_label} {'.' * padding} loaded"

        def update_log():
            self.rich_log.write(log_text)

        self.app.call_from_thread(update_log)

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
    def run_io_worker(self, arg_id: str) -> None:
        io_class = getattr(self.app.chezmoi, arg_id)
        io_class.update()
        self.log_text(f'chezmoi {arg_id.replace("_", " ")}')

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.workers
            if worker.group == "io_workers"
        ):
            self.dismiss()

    def on_mount(self) -> None:

        animated_fade = self.query_exactly_one(AnimatedFade)
        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )

        if not INIT_CFG.chezmoi_found:
            self.log_unavailable_chezmoi_command()
            return

        # first run chezmoi doctor, most expensive command
        self.run_io_worker("doctor")
        self.long_commands.pop("doctor")

        for arg_id in self.long_commands:
            self.run_io_worker(arg_id)
