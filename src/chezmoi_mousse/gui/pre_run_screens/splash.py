import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

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

from chezmoi_mousse import AppType, LogUtils, ManagedPaths, ReadCmd, VerbArgs

if TYPE_CHECKING:
    from chezmoi_mousse import CommandResults

__all__ = ["LoadingScreen", "ParsedConfig", "SplashData"]

SPLASH_COMMANDS = [
    ReadCmd.cat_config,
    ReadCmd.doctor,
    ReadCmd.dump_config,
    ReadCmd.ignored,
    ReadCmd.managed_dirs,
    ReadCmd.managed_files,
    ReadCmd.status_dirs,
    ReadCmd.status_files,
    ReadCmd.status_paths,
    ReadCmd.template_data,
]

PRETTY_SPLASH_COMMANDS = [
    LogUtils.pretty_cmd_str(splash_command.value)
    for splash_command in SPLASH_COMMANDS
]


@dataclass(slots=True)
class ParsedConfig:
    dest_dir: Path
    git_autoadd: bool
    source_dir: Path
    git_autocommit: bool
    git_autopush: bool


@dataclass(slots=True)
class SplashData:
    cat_config: str
    doctor: str
    exectuded_commands: list[str]
    ignored: str
    managed_paths: ManagedPaths
    parsed_config: ParsedConfig
    template_data: str


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
LOADED_SUFFIX = "loaded"
NOT_FOUND_SUFFIX = "not found"


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
dump_config: ParsedConfig | None = None
ignored: str = ""
managed_dirs: str = ""
managed_files: str = ""
status_dirs: str = ""
status_files: str = ""
status_paths: str = ""
template_data: str = ""


class AnimatedFade(Static):

    def render_lines(self, crop: Region) -> list[Strip]:
        FADE_LINE_STYLES.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=FADE_LINE_STYLES[y])])


class LoadingScreen(Screen[SplashData | None], AppType):

    def __init__(self, chezmoi_found: bool) -> None:
        self.chezmoi_found = chezmoi_found
        self.fade_timer: Timer
        self.all_workers_timer: Timer
        super().__init__()

    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                yield Center(AnimatedFade())
                yield Center(RichLog())

    @work(thread=True, group="io_workers")
    def run_read_cmd(self, splash_cmd: ReadCmd) -> None:

        splash_log = self.query_exactly_one(RichLog)

        if not self.chezmoi_found:
            cmd_text = "chezmoi command"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            log_text = f"{cmd_text} {'.' * padding} {NOT_FOUND_SUFFIX}"
            splash_log.write(log_text)
            return

        cmd_result: "CommandResults" = self.app.chezmoi.read(splash_cmd)
        globals()[splash_cmd.name] = cmd_result.std_out
        cmd_text = cmd_result.pretty_cmd.replace(
            VerbArgs.include_dirs.value, "dirs"
        ).replace(VerbArgs.include_files.value, "files")
        padding = LOG_PADDING_WIDTH - len(cmd_text)
        log_text = f"{cmd_text} {'.' * padding} {LOADED_SUFFIX}"
        splash_log.write(log_text)
        if splash_cmd.name == ReadCmd.dump_config.name:
            parsed_config = json.loads(cmd_result.std_out)
            globals()["parsed_config"] = ParsedConfig(
                dest_dir=Path(parsed_config["destDir"]),
                git_autoadd=parsed_config["git"]["autoadd"],
                source_dir=Path(parsed_config["sourceDir"]),
                git_autocommit=parsed_config["git"]["autocommit"],
                git_autopush=parsed_config["git"]["autopush"],
            )

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "io_workers"
        ):
            if self.chezmoi_found is False:
                self.dismiss(None)
                return

            globals()["managed_paths"] = ManagedPaths(
                managed_dirs_stdout=globals()["managed_dirs"],
                managed_files_stdout=globals()["managed_files"],
                status_dirs_stdout=globals()["status_dirs"],
                status_files_stdout=globals()["status_files"],
                status_paths_stdout=globals()["status_paths"],
            )

            self.dismiss(
                SplashData(
                    cat_config=globals()["cat_config"],
                    doctor=globals()["doctor"],
                    exectuded_commands=PRETTY_SPLASH_COMMANDS,
                    ignored=globals()["ignored"],
                    managed_paths=globals()["managed_paths"],
                    parsed_config=globals()["parsed_config"],
                    template_data=globals()["template_data"],
                )
            )

    def on_mount(self) -> None:
        middle_container = self.query_one(Middle)
        middle_container.styles.width = FADE_WIDTH
        animated_fade = self.query_exactly_one(AnimatedFade)
        animated_fade.styles.height = FADE_HEIGHT
        rich_log = self.query_exactly_one(RichLog)
        rich_log.styles.width = "auto"
        rich_log.styles.color = "#6DB2FF"
        rich_log.styles.margin = 2
        if self.chezmoi_found:
            rich_log.styles.height = len(SPLASH_COMMANDS)
        else:
            rich_log.styles.height = 1

        if not self.chezmoi_found:
            self.run_read_cmd("")
        else:
            for cmd in SPLASH_COMMANDS:
                self.run_read_cmd(cmd)

        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )
