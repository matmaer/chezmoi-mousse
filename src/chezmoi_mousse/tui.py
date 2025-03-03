from dataclasses import dataclass
import json
import subprocess
import tomllib
from collections import deque

from textual import work
from textual.app import App, ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    # Pretty,
    RichLog,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import FLOW_DIAGRAM, SPLASH, oled_dark_zen


@dataclass
class InputOutput:
    long_command: list[str]
    std_out: str = "initial std_out value"

    @property
    def py_out(self):
        failures = {}
        std_out = self.std_out.strip()
        if std_out == "":
            failures["std_out"] = "empty std_out nothing to decode"
        try:
            return json.loads(std_out)
        except json.JSONDecodeError:
            failures["json"] = "std_out json.JSONDecodeError"
        try:
            return tomllib.loads(std_out)
        except tomllib.TOMLDecodeError:
            failures["toml"] = "std_out tomllib.TOMLDecodeError"
            # check how many "\n" newlines are found in the output
        if std_out.count("\n") > 0:
            return std_out.splitlines()
        return std_out

    @property
    def label(self):
        return " ".join(
            [w for w in self.long_command if not w.startswith("-")]
        )

    def _subprocess_run(self):
        """Runs the subprocess call and sets std_out."""
        result = subprocess.run(
            self.long_command,
            capture_output=True,
            check=True,  # raises exception for any non-zero return code
            shell=False,  # mitigates shell injection risk
            text=True,  # returns stdout as str instead of bytes
            timeout=2,
        )
        self.std_out = result.stdout

    def update(self):
        """Re-run the subprocess call, don't return anything."""
        self._subprocess_run()

    def updated_std_out(self):
        """Re-run subprocess call and return std_out."""
        self._subprocess_run()
        return self.std_out

    def updated_py_out(self):
        """Re-run subprocess call and return py_out."""
        self._subprocess_run()
        return self.py_out


class Chezmoi:

    cat_config: InputOutput = None
    data: InputOutput = None
    doctor: InputOutput = None
    dump_config: InputOutput = None
    git_log: InputOutput = None
    git_status: InputOutput = None
    ignored: InputOutput = None
    managed: InputOutput = None
    status: InputOutput = None
    unmanaged: InputOutput = None

    def __init__(self):
        self.base = [
            "chezmoi",
            "--no-pager",
            "--color=false",
            "--no-tty",
            "--progress=false",
        ]
        self.subs = {
            "cat_config": ["cat-config"],
            "data": ["data", "--format=json"],
            "doctor": ["doctor"],
            "dump_config": ["dump-config", "--format=json"],
            "git_log": ["git", "log", "--", "--oneline"],
            "git_status": ["git", "status"],
            "ignored": ["ignored"],
            "managed": ["managed", "--path-style=absolute"],
            "status": ["status", "--parent-dirs"],
            "unmanaged": ["unmanaged", "--path-style=absolute"],
        }

        for arg_id, sub_cmd in self.subs.items():
            setattr(self, arg_id, InputOutput(self.base + sub_cmd))

    @property
    def arg_ids(self):
        """Return the list of arg_ids."""
        return list(self.subs.keys())

    def updated_input_output(self, arg_id):
        """Update and return the InputOutput instance in this Chezmoi class."""
        getattr(self, arg_id).update()
        return getattr(self, arg_id)


chezmoi = Chezmoi()


class AnimatedFade(Widget):

    line_styles: deque[Style]

    def __init__(self) -> None:
        super().__init__(id="animated-fade")
        self.styles.height = len(SPLASH)
        self.styles.width = len(max(SPLASH, key=len))

    def create_fade(self) -> deque[Style]:
        start_color = self.app.current_theme.primary
        end_color = self.app.current_theme.accent
        fade = [Color.parse(start_color)] * 5
        gradient = Gradient.from_colors(start_color, end_color, quality=5)
        fade.extend(gradient.colors)
        gradient.colors.reverse()
        fade.extend(gradient.colors)
        return deque([Style(color=color.hex, bold=True) for color in fade])

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

    def on_mount(self) -> None:
        self.line_styles = self.create_fade()
        self.set_interval(interval=0.11, callback=self.refresh)


class LoadingScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(id="loader-log", max_lines=11))
            yield Center(
                Button(
                    id="to-continue",
                    label="Press any key to continue",
                    disabled=True,
                )
            )

    @work(thread=True)
    def _run(self, arg_id) -> None:
        getattr(chezmoi, arg_id).update()
        label = getattr(chezmoi, arg_id).label
        padding = 32 - len(label)
        line = f"{label} {'.' * padding} loaded"
        self.query_one("#loader-log").write(line)

    def on_mount(self) -> None:
        for arg_id in chezmoi.arg_ids:
            self._run(arg_id)

    def on_key(self) -> None:
        self.app.pop_screen()


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            "Diagram",
            # "Doctor",
            "Dump-Config",
            # "Chezmoi-Status",
            # "Managed-Files",
            # "Template-Data",
            # "Cat-Config",
            # "Git-Log",
            # "Ignored",
            # "Git-Status",
            # "Unmanaged",
        ):
            yield Static(FLOW_DIAGRAM, id="diagram")
            # yield ChezmoiDoctor(chezmoi.doctor.py_out)
            yield Static(chezmoi.dump_config.py_out)
            # yield ChezmoiStatus(chezmoi.status.py_out)
            # yield ManagedFiles(chezmoi.managed.py_out)
            # yield Pretty(chezmoi.data.py_out)
            # yield Pretty(chezmoi.cat_config.py_out)
            # yield Pretty(chezmoi.git_log.py_out)
            # yield Pretty(chezmoi.ignored.py_out)
            # yield Pretty(chezmoi.status.py_out)
            # yield Pretty(chezmoi.unmanaged.py_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
        self.push_screen("loading")
