import json
from collections import deque
from pathlib import Path
from subprocess import CompletedProcess, run

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

from chezmoi_mousse import (
    IDS,
    AppType,
    Chezmoi,
    CommandResult,
    OperateBtn,
    OperateData,
    ParsedConfig,
    ReadCmd,
    SplashData,
    VerbArgs,
)
from chezmoi_mousse.shared import ContentsView, DiffView, GitLogPath

from .main_tabs import MainScreen
from .operate_chezmoi import OperateChezmoiScreen
from .tabs.add_tab import AddTab
from .tabs.common.switchers import ViewSwitcher
from .tabs.common.trees import TreeBase

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
    ReadCmd.verify,
]

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


cat_config: "CommandResult | None" = None
doctor: "CommandResult | None" = None
dump_config: "CommandResult | None" = None
git_log: "CommandResult | None" = None
ignored: "CommandResult | None" = None
managed_dirs: "CommandResult | None" = None
managed_files: "CommandResult | None" = None
parsed_config: "ParsedConfig | None" = None
status_dirs: "CommandResult | None" = None
status_files: "CommandResult | None" = None
template_data: "CommandResult | None" = None
verify: "CommandResult | None" = None


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()

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
            [
                Style(color=color, bgcolor="#000000", bold=True)
                for color in fade
            ]
        )
        self.fade_line_styles.rotate(-2)
        self.set_interval(
            name="refresh_self", interval=0.1, callback=self.refresh
        )

    def render_lines(self, crop: Region) -> list[Strip]:
        self.fade_line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.fade_line_styles[y])])


class SplashLog(RichLog):
    def __init__(self) -> None:
        super().__init__(id=IDS.splash.logger.splash, markup=True)

    def on_mount(self) -> None:
        self.styles.height = len(SPLASH_COMMANDS)
        self.styles.width = "auto"
        self.styles.margin = 2


class SplashScreen(Screen[SplashData | None], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.splash_log: SplashLog  # set in on_mount
        self.init_cmd_needed: bool = False

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

    async def on_mount(self) -> None:
        self.check_workers_timer = self.set_interval(
            interval=2, callback=self.all_workers_finished
        )
        self.splash_log = self.query_one(IDS.splash.logger.splash_q, SplashLog)
        if self.app.chezmoi_found is False:
            self.splash_log.styles.height = 1
            cmd_text = "chezmoi command"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            self.splash_log.write(f"{cmd_text} {'.' * padding} not found")
            return

        status_worker = self.run_io_worker(ReadCmd.status_files)
        await status_worker.wait()
        if status_worker.state == WorkerState.SUCCESS:
            if type(globals()["status_files"].exit_code) is not int:
                raise RuntimeError("status_files exit_code is not an int")
            if (
                globals()["status_files"].exit_code != 0
                or self.app.force_init_operation is True
            ):
                self.app.force_init_operation = False
                self.app.operate_data = OperateData(
                    btn_enum=OperateBtn.init_repo,
                    btn_label=OperateBtn.init_repo.init_new_label,
                    btn_tooltip=OperateBtn.init_repo.initial_tooltip,
                )
                # Run io workers for OperateScreen init commands
                self.run_io_worker(ReadCmd.doctor)
                self.run_io_worker(ReadCmd.template_data)
                self.init_cmd_needed = True
                return
            for splash_cmd in SPLASH_COMMANDS:
                if splash_cmd == ReadCmd.status_files:
                    continue
                self.run_io_worker(splash_cmd)
        else:
            raise RuntimeError(
                "status_files worker did not complete successfully"
            )

    @work(thread=True, group="io_workers")
    def run_io_worker(self, splash_cmd: ReadCmd) -> None:
        result: CompletedProcess[str] = run(
            splash_cmd.value,
            capture_output=True,
            shell=False,
            text=True,
            timeout=2,
        )
        cmd_result = CommandResult(
            completed_process=result, read_cmd=splash_cmd
        )
        cmd_text = cmd_result.pretty_cmd
        globals()[splash_cmd.name] = cmd_result
        if splash_cmd == ReadCmd.dump_config:
            parsed_config = json.loads(cmd_result.std_out)
            globals()["parsed_config"] = ParsedConfig(
                dest_dir=Path(parsed_config["destDir"]),
                git_autoadd=parsed_config["git"]["autoadd"],
                source_dir=Path(parsed_config["sourceDir"]),
                git_autocommit=parsed_config["git"]["autocommit"],
                git_autopush=parsed_config["git"]["autopush"],
            )
        elif splash_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            cmd_text = cmd_result.pretty_cmd.replace(
                VerbArgs.include_dirs.value, "dirs"
            ).replace(VerbArgs.include_files.value, "files")
        padding = LOG_PADDING_WIDTH - len(cmd_text)
        log_text = f"{cmd_text} {'.' * padding} {LOADED_SUFFIX}"
        if cmd_result.exit_code == 0:
            color = self.app.theme_variables["text-primary"]
        elif cmd_result.exit_code == 1:
            if splash_cmd == ReadCmd.verify:
                color = self.app.theme_variables["text-primary"]
            else:
                color = self.app.theme_variables["text-warning"]
        else:
            color = self.app.theme_variables["text-error"]
        self.app.call_from_thread(
            self.splash_log.write, f"[{color}]{log_text}[/{color}]"
        )

    @work(name="update_app")
    async def update_app(self):
        self.app.splash_data = SplashData(
            cat_config=globals()["cat_config"],
            doctor=globals()["doctor"],
            git_log=globals()["git_log"],
            ignored=globals()["ignored"],
            parsed_config=globals()["parsed_config"],
            template_data=globals()["template_data"],
            verify=globals()["verify"],
            init_needed=self.init_cmd_needed,
        )
        self.app.chezmoi = Chezmoi(
            dev_mode=self.app.dev_mode,
            managed_dirs=globals()["managed_dirs"],
            managed_files=globals()["managed_files"],
            status_dirs=globals()["status_dirs"],
            status_files=globals()["status_files"],
        )
        if self.init_cmd_needed is True:
            return
        dest_dir = globals()["parsed_config"].dest_dir
        AddTab.destDir = dest_dir
        ContentsView.destDir = dest_dir
        DiffView.destDir = dest_dir
        GitLogPath.destDir = dest_dir
        MainScreen.destDir = dest_dir
        TreeBase.destDir = dest_dir
        ViewSwitcher.destDir = dest_dir
        OperateChezmoiScreen.git_autocommit = globals()[
            "parsed_config"
        ].git_autocommit
        OperateChezmoiScreen.git_autopush = globals()[
            "parsed_config"
        ].git_autopush
        self.app.install_screen(MainScreen(), name="main_screen")  # type: ignore[arg-type]

    def all_workers_finished(self) -> None:
        if self.app.chezmoi_found is False:
            self.dismiss(None)
            return
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "io_workers"
        ):
            self.check_workers_timer.stop()
            update_app_worker = self.update_app()
            if update_app_worker.state == WorkerState.SUCCESS:
                self.dismiss()
            else:
                raise RuntimeError(
                    "update_app worker did not complete successfully"
                )
