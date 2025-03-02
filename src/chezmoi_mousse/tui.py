from collections import deque

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Pretty, RichLog, Static, TabbedContent

from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.widget import Segment, Strip, Style, Widget

from chezmoi_mousse.commands import Utils, InputOutput
from chezmoi_mousse.splash import FLOW_DIAGRAM, SPLASH, oled_dark_zen




class Chezmoi(Utils):

    name = "chezmoi"
    base = [name] + [
        "--no-pager",
        "--color=false",
        "--no-tty",
        "--progress=false",
    ]
    subs = [
        ["cat-config"],
        ["data", "--format=json"],
        ["doctor"],
        ["dump-config", "--format=json"],
        ["git", "log", "--", "--oneline"],
        ["git", "status"],
        ["ignored"],
        ["managed", "--path-style=absolute"],
        ["status", "--parent-dirs"],
        ["unmanaged", "--path-style=absolute"],
    ]

    @property
    def all_long_commands(self):
        return [self.base + sub for sub in self.subs]

    def __init__(self):
        for long_cmd in self.all_long_commands:
            arg_id = Utils.get_arg_id(long_command=long_cmd)
            setattr(self, arg_id, InputOutput)

chezmoi = Chezmoi()


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


class LoadingScreen(Widget):

    def __init__(self):
        super().__init__(id="loader-screen")

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(id="loader-log", max_lines=11))
        # yield Link(id="to-continue", text="Press any key to continue")

    @work(thread=True)
    def _run(self, arg_id: str, line: str) -> None:
        chezmoi_command = getattr(chezmoi, arg_id)
        chezmoi_command.update()
        self.query_one("#loader-log").write(line)

    def on_mount(self) -> None:
        # self.title = "-  c h e z m o i  m o u s s e  -"
        for long_cmd in chezmoi.long_commands: # pylint: disable=no-member
            arg_id = Utils.get_arg_id(long_cmd)
            setattr(chezmoi, arg_id, InputOutput(long_cmd, arg_id))
            label = getattr(chezmoi, arg_id).label
            padding = 32 - len(label)
            line = f"{label} {'.' * padding} loaded"
            self._run(arg_id, line)


class ChezmoiTUI(App):

    CSS_PATH = "tui.tcss"

    BINDINGS = [
        ("s, S", "toggle_sidebar", "Toggle Sidebar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(
            "Diagram",
            # "Doctor",
            "Dump-Config",
            # "Chezmoi-Status",
            # "Managed-Files",
            "Template-Data",
            "Cat-Config",
            "Git-Log",
            "Ignored",
            "Git-Status",
            "Unmanaged",
        ):
            # pylint: disable=no-member
            yield Static(FLOW_DIAGRAM, id="diagram")
            # yield ChezmoiDoctor(chezmoi.doctor.py_out)
            yield Pretty(chezmoi.dump_config.py_out)
            # yield ChezmoiStatus(chezmoi.status.py_out)
            # yield ManagedFiles(chezmoi.managed.py_out)
            yield Pretty(chezmoi.data.py_out)
            yield Pretty(chezmoi.cat_config.py_out)
            yield Pretty(chezmoi.git_log.py_out)
            yield Pretty(chezmoi.ignored.py_out)
            yield Pretty(chezmoi.status.py_out)
            yield Pretty(chezmoi.unmanaged.py_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "- o p e r a t e -"
        self.register_theme(oled_dark_zen)
        self.theme = "oled-dark-zen"
