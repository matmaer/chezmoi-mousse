import json
import os
from collections import deque
from dataclasses import dataclass, fields
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import Any

from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.color import Gradient
from textual.containers import (
    Center,
    Horizontal,
    Middle,
    Vertical,
    VerticalGroup,
)
from textual.geometry import Region
from textual.screen import Screen
from textual.strip import Strip
from textual.timer import Timer
from textual.widgets import (
    Button,
    Collapsible,
    Label,
    Link,
    Pretty,
    RichLog,
    Static,
    Tree,
)
from textual.worker import WorkerState

from chezmoi_mousse import (
    AppType,
    Canvas,
    Chars,
    ReadCmd,
    SubTitles,
    Tcss,
    VerbArgs,
)
from chezmoi_mousse.gui.rich_logs import LogUtils

type ParsedJson = dict[str, Any]

__all__ = ["InstallHelp", "LoadingScreen"]


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
    dump_config: ParsedConfig
    ignored: str
    managed_dirs: str
    managed_files: str
    status_dirs: str
    status_files: str
    status_paths: str
    template_data: str


class Strings(StrEnum):
    exit_button_id = "exit_button"
    chezmoi_docs_link_id = "chezmoi_docs_link"


class CommandsTree(Tree[ParsedJson]):
    ICON_NODE = Chars.right_triangle
    ICON_NODE_EXPANDED = Chars.down_triangle

    def __init__(self) -> None:
        super().__init__(label=" Install chezmoi ")


class InstallHelp(Screen[None], AppType):

    BINDINGS = [Binding(key="escape", action="exit_application", show=False)]

    def __init__(self, chezmoi_found: bool) -> None:
        self.chezmoi_found = chezmoi_found
        super().__init__(id=Canvas.install_help, classes=Tcss.screen_base.name)
        self.path_env_list: list[str] = []
        self.pkg_root: Path | None = None

    def compose(self) -> ComposeResult:
        if self.chezmoi_found is True:
            return
        with Vertical(classes=Tcss.install_help.name):
            yield Center(Label(("Chezmoi is not installed or not found.")))
            yield Collapsible(
                Pretty("PATH variable is empty or not set."),
                title="'chezmoi' command not found in any search path",
            )

            with Center():
                with Horizontal():
                    yield CommandsTree()
                    with VerticalGroup():
                        yield Link(
                            "chezmoi.io/install",
                            url="https://chezmoi.io/install",
                            id=Strings.chezmoi_docs_link_id,
                        )
                        yield Button(
                            "exit app",
                            id=Strings.exit_button_id,
                            variant="primary",
                            flat=True,
                        )

    def on_mount(self) -> None:
        if self.chezmoi_found is False:
            self.border_subtitle = SubTitles.escape_exit_app
            self.pkg_root = self.get_pkg_root()
            self.update_path_widget()
            self.populate_tree()

    def get_pkg_root(self) -> Path:
        return (
            Path(str(files(__package__)))
            if __package__
            else Path(__file__).resolve().parent
        )

    def update_path_widget(self) -> None:
        self.path_env = os.environ.get("PATH")
        entry_sep = ";" if os.name == "nt" else ":"
        if self.path_env is not None:
            self.path_env_list = self.path_env.split(entry_sep)
            pretty_widget = self.query_exactly_one(Pretty)
            pretty_widget.update(self.path_env_list)

    def populate_tree(self) -> None:
        if self.pkg_root is None:
            return
        help_tree: CommandsTree = self.query_exactly_one(CommandsTree)
        data_file: Path = Path.joinpath(
            self.pkg_root, "data", "chezmoi_install_commands.json"
        )
        install_help: ParsedJson = json.loads(data_file.read_text())
        help_tree.show_root = False
        for k, v in install_help.items():
            help_tree.root.add(label=k, data=v)
        for child in help_tree.root.children:
            assert child.data is not None
            install_commands: dict[str, str] = child.data
            for k, v in install_commands.items():
                child_label = Text(k, style="warning")
                new_child = child.add(label=child_label)
                cmd_label = Text(v)
                new_child.add_leaf(label=cmd_label)

    @on(Button.Pressed)
    def exit_application(self, event: Button.Pressed) -> None:
        self.app.exit()

    def action_exit_application(self) -> None:
        self.app.exit()


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
    def run_read_cmd(self, field_name: str) -> None:

        splash_log = self.query_exactly_one(RichLog)

        if not self.chezmoi_found:
            cmd_text = "chezmoi command"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            log_text = f"{cmd_text} {'.' * padding} {NOT_FOUND_SUFFIX}"
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
        log_text = f"{cmd_text} {'.' * padding} {LOADED_SUFFIX}"
        splash_log.write(log_text)
        if field_name == "dump_config":
            parsed_config = json.loads(cmd_output)
            globals()["dump_config"] = ParsedConfig(
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

            self.dismiss(
                SplashData(
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
        middle_container = self.query_one(Middle)
        middle_container.styles.width = FADE_WIDTH
        animated_fade = self.query_exactly_one(AnimatedFade)
        animated_fade.styles.height = FADE_HEIGHT
        rich_log = self.query_exactly_one(RichLog)
        rich_log.styles.width = "auto"
        rich_log.styles.color = "#6DB2FF"
        rich_log.styles.margin = 2
        if self.chezmoi_found:
            rich_log.styles.height = len(fields(SplashData))
        else:
            rich_log.styles.height = 1

        if not self.chezmoi_found:
            self.run_read_cmd("")
        else:
            for field_name in [field.name for field in fields(SplashData)]:
                self.run_read_cmd(field_name)

        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )
