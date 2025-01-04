""" Contains the Textual App class for the TUI. """

from pathlib import Path
from typing import Iterable

from textual import on
from textual.app import App, ComposeResult, Widget
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (Button, DataTable, DirectoryTree, Footer, Header,
                             Label, Pretty, RichLog, Static, TabbedContent)

from chezmoi_mousse.blocks import VISUAL_DIAGRAM
from chezmoi_mousse.operate import ChezmoiCommands

chezmoi = ChezmoiCommands()

CM_CONFIG_DUMP = chezmoi.dump_config()


class MainMenu(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("Main Menu")
        yield Button(
            label="Local Info",
            id="local_info",
        )
        yield Button(
            label="Chezmoi Overview",
            id="inspect",
        )
        yield Button(
            label="Operate Chezmoi",
            id="operate",
        )
        yield Button(
            label="Standard Output",
            id="show_stdout",
        )
        yield Button(
            label="Help",
            id="app_help",
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
    def __init__(self, rootpath=str):
        super().__init__(rootpath)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        managed = chezmoi.managed()
        # convert all strings to Path objects
        filter_list = [Path(entry) for entry in managed]
        # tell DirectoryTree what to show
        return [path for path in paths if path in filter_list]


class Help(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield Static(HELP_TEXT)


# class ChezmoiDoctor(Widget):

#     def __init__(self, doctor_output: list):
#         super().__init__()
#         self.doctor_output = doctor_output

#     def compose(self) -> ComposeResult:
#         yield DataTable()

#     def on_mount(self) -> None:
#         table = self.query_one(DataTable)
#         headers = (self.doctor_output.pop(0))
#         headers = tuple(headers.split(maxsplit=2))
#         table.add_columns(headers)

#         for row in self.doctor_output:
#             table.add_row(row.split(maxsplit=2))

        # rows_by_column = [row for row in self.doctor_output]
        # table.add_rows(rows_by_column)

        # table.add_row(str(number), str(number * 2), str(number * 3))
        # table.fixed_rows = 2
        # table.fixed_columns = 1
        # table.cursor_type = "row"
        # table.zebra_stripes = True

class ChezmoiTUI(App):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("m", "local_config", "Local Info"),
        Binding("m", "differences", "Differences"),
        Binding("m", "operate", "Operate Chezmoi"),
        Binding("s", "toggle_richlogsidebar", "Standard Output"),
        Binding("q", "quit", "Quit"),
    ]
    CSS_PATH = "tui.tcss"
    show_richlog = reactive(False)

    globaldict = globals().copy()

    globaldict.pop('__builtins__')
    globaldict.pop('VISUAL_DIAGRAM')

    def rlog(self, to_print: str) -> None:
        richlog = self.query_one(RichLog)
        richlog.write(to_print)

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
                "Help",
            ):
                yield ManagedFiles(CM_CONFIG_DUMP["destDir"])
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield DataTable()
                    # yield ChezmoiDoctor(chezmoi.doctor())
                with VerticalScroll():
                    yield Pretty(chezmoi.dump_config())
                with VerticalScroll():
                    yield Pretty(chezmoi.data())
                with VerticalScroll():
                    yield Pretty(chezmoi.cat_config())
                with VerticalScroll():
                    yield Pretty(self.globaldict)
                with VerticalScroll():
                    yield Pretty(locals())
                yield VerticalScroll()

            yield RichLogSidebar()
        yield Footer()

    def on_mount(self) -> None:
        doctor_output = chezmoi.doctor()

        table = self.query_one(DataTable)
        table.add_columns(*doctor_output.pop(0).split())
        table.add_rows([row.split(maxsplit=2) for row in doctor_output])

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


HELP_TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur.

Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.
"""
