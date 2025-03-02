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
    Pretty,
    RichLog,
    Static,
    TabbedContent,
)

from chezmoi_mousse import chezmoi
from chezmoi_mousse.commands import Utils
from chezmoi_mousse.splash import FLOW_DIAGRAM, SPLASH, oled_dark_zen


class AnimatedFade(Widget):

    line_styles: deque[Style]

    def __init__(self) -> None:
        super().__init__(id="animated-fade")
        self.styles.height = len(SPLASH)
        self.styles.width = len(max(SPLASH, key=len))
        self.line_styles: deque[Style] = self.create_fade()

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
        self.set_interval(interval=0.11, callback=self.refresh)


class LoadingScreen(Screen):

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(id="loader-log", max_lines=11))
            yield Center(
                Button(id="to-continue", label="Press any key to continue")
            )

    @work(thread=True)
    def _run(self, command_dataclass, line: str) -> None:
        command_dataclass.update()
        self.query_one("#loader-log").write(line)

    def on_mount(self) -> None:

        for long_cmd in chezmoi.all_long_commands:  # pylint: disable=no-member
            arg_id = Utils.get_arg_id(long_cmd)
            command_dataclass = getattr(chezmoi, arg_id)
            padding = 32 - len(command_dataclass.label)
            line = f"{command_dataclass.label} {'.' * padding} loaded"
            self._run(command_dataclass, line)

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
            # pylint: disable=no-member
            yield Static(FLOW_DIAGRAM, id="diagram")
            # yield ChezmoiDoctor(chezmoi.doctor.py_out)
            yield Pretty(chezmoi.dump_config.py_out)
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
