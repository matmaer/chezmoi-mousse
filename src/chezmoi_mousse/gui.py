"""Contains the main GUI application where the App class is being subclassed
and the MainScreen class which is rendered after the LoadingScreen has
completed running each chezmoi command."""

from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.lazy import Lazy
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import (
    Footer,
    Header,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

import chezmoi_mousse.chezmoi
from chezmoi_mousse import BURGER, FLOW
from chezmoi_mousse.main_tabs import AddTab, ApplyTab, DoctorTab, ReAddTab
from chezmoi_mousse.splash import LoadingScreen


class CommandLog(RichLog):
    def add(self, chezmoi_io: tuple[list, str]) -> None:
        time_stamp = datetime.now().strftime("%H:%M:%S")
        # Turn the full command list into string, remove elements not useful
        # to display in the log
        trimmed_cmd = [
            _
            for _ in chezmoi_io[0]
            if _
            not in (
                "--no-pager"
                "--color=off"
                "--no-tty"
                "--format=json"
                "--path-style=absolute"
                "--path-style=source-absolute"
            )
        ]
        pretty_cmd = " ".join(trimmed_cmd)
        self.write(f"{time_stamp} {pretty_cmd}")
        if chezmoi_io[1]:
            self.write(chezmoi_io[1])
        else:
            self.write("Output: to be implemented")


class MainScreen(Screen):

    def __init__(self, splash_command_log: list[tuple[list, str]]) -> None:
        super().__init__()
        self.splash_command_log = splash_command_log

    def compose(self) -> ComposeResult:
        yield Header(icon=BURGER)
        with TabbedContent():
            with TabPane("Apply", id="apply_tab_pane"):
                yield ApplyTab(id="apply_tab")
            with TabPane("Re-Add", id="re_add_tab_pane"):
                yield Lazy(ReAddTab(id="re_add_tab"))
            with TabPane("Add", id="add_tab_pane"):
                yield Lazy(AddTab(id="add_tab"))
            with TabPane("Doctor", id="doctor_tab_pane"):
                yield Lazy(DoctorTab(id="doctor_tab"))
            with TabPane("Diagram", id="diagram_tab_pane"):
                yield ScrollableContainer(Static(FLOW, id="flow_diagram"))
            with TabPane("Log", id="rich_log_tab_pane"):
                yield CommandLog(
                    id="command_log", highlight=True, max_lines=20000
                )
        yield Footer()

    def on_mount(self) -> None:
        command_log = self.query_one("#command_log", CommandLog)
        for cmd in self.splash_command_log:
            command_log.add(cmd)

        def log_callback(chezmoi_io: tuple[list, str]) -> None:
            command_log.add(chezmoi_io)

        global command_log_callback
        chezmoi_mousse.chezmoi.command_log_callback = log_callback


chezmoi_mousse_dark = Theme(
    name="chezmoi-mousse-dark",
    dark=True,
    accent="#F187FB",
    background="#000000",
    error="#ba3c5b",  # textual dark
    foreground="#DEDAE1",
    primary="#0178D4",  # textual dark
    secondary="#004578",  # textual dark
    surface="#101010",  # see also textual/theme.py
    success="#4EBF71",  # textual dark
    warning="#ffa62b",  # textual dark
)


class ChezmoiGUI(App):

    CSS_PATH = "gui.tcss"

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(chezmoi_mousse_dark)
        self.theme = "chezmoi-mousse-dark"
        self.push_screen(LoadingScreen(), self.push_main_screen)

    def push_main_screen(self, splash_command_log) -> None:
        self.push_screen(MainScreen(splash_command_log))
