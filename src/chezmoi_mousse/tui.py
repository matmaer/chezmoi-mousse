""" Contains the Textual App class for the TUI. """

from pathlib import Path
from typing import Iterable

from textual import on
from textual.app import App, ComposeResult, Widget
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (Button, DirectoryTree, Footer, Header, Label,
                             Pretty, RichLog, Static, TabbedContent)

from chezmoi_mousse.blocks import VISUAL_DIAGRAM
from chezmoi_mousse.operate import ChezmoiCommands

CM_CONFIG_DUMP = ChezmoiCommands().dump_config()


class MainMenu(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Main Menu")
        yield Button(
            label="Inspect",
            id="inspect",
        )
        yield Button(
            label="Operate",
            id="operate",
        )
        yield Button(
            label="Output",
            id="show_stdout",
        )
        yield Button(
            label="Help",
            id="app_help",
        )
        yield Button(
            label="Exit",
            id="clean_exit",
        )


class RichLogSidebar(Widget):
    def compose(self) -> ComposeResult:
        yield RichLog(
            id="richlog",
            highlight=True,
            wrap=False,
            markup=True,
        )


class ManagedFiles(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed = ChezmoiCommands().managed()
        # convert all strings to Path objects
        filter_list = [Path(entry) for entry in managed]
        # the actual filter with a list comprehension
        return [path for path in paths if path in filter_list]


class ChezmoiTUI(App):
    BINDINGS = [
        Binding("m", "operate", "Menu"),
        Binding("s", "toggle_richlogsidebar", "Output"),
        Binding("escape", "app.pop_screen", "Back"),
        Binding("q", "quit", "Quit"),
    ]
    CSS_PATH = "tui.tcss"
    show_richlog = reactive(False)

    def rlog(self, to_print: str) -> None:
        richlog = self.query_one(RichLog)
        richlog.write(to_print)

    def chezmoi_doctor(self):
        return ChezmoiCommands().doctor()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield MainMenu()
            with TabbedContent(
                "Managed",
                "Diagram",
                "Doctor",
                "Config-dump",
                "Data",
                "Config-cat",
                "Globals",
                "Locals",
            ):
                # yield DirectoryTree(CM_CONFIG_DUMP["destDir"])
                yield ManagedFiles("/home/mm")
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield Pretty(ChezmoiCommands().doctor())
                with VerticalScroll():
                    yield Pretty(ChezmoiCommands().dump_config())
                with VerticalScroll():
                    yield Pretty(ChezmoiCommands().data())
                with VerticalScroll():
                    yield Pretty(ChezmoiCommands().cat_config())
                with VerticalScroll():
                    yield Pretty(globals())
                with VerticalScroll():
                    yield Pretty(locals())

            yield RichLogSidebar()
        yield Footer()

    @on(Button.Pressed, "#inspect")
    def enter_inspect_mode(self):
        self.rlog("[cyan]nspect mode[/]")
        self.rlog("[red]Inspect mode is not yet implemented[/]")

    @on(Button.Pressed, "#operate")
    def enter_operate_mode(self):
        self.rlog("[cyan]operate mode[/]")
        self.rlog("[red]Operate mode is not yet implemented[/]")

    @on(Button.Pressed, "#show_stdout")
    def show_chezmoi_managed(self):
        self.rlog("[cyan]Show stdout[/]")
        self.rlog("[red]Show stdout is not yet implemented[/]")

    @on(Button.Pressed, "#app_help")
    def show_app_help(self):
        self.rlog("[cyan]App help[/]")
        self.rlog("[red]App help is not yet implemented[/]")

    @on(Button.Pressed, "#clean_exit")
    def clean_exit(self):
        self.rlog("[cyan]Clean exit[/]")
        self.rlog("[red]Clean exit is not yet implemented[/]")

    def action_toggle_mainmenu(self):
        self.query_one(MainMenu).toggle_class("-hidden")

    def action_toggle_richlogsidebar(self) -> None:
        self.show_richlog = not self.show_richlog

    def watch_show_richlog(self, show_richlog: bool) -> None:
        # Set or unset visible class when reactive changes.
        self.query_one(RichLogSidebar).set_class(show_richlog, "-visible")
