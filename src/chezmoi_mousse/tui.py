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

from chezmoi_mousse import chezmoi
from chezmoi_mousse.text_blocks import HELP_TEXT, VISUAL_DIAGRAM

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
    def __init__(self):
        super().__init__(CM_CONFIG_DUMP["destDir"])
        self.managed = [Path(entry) for entry in chezmoi.managed()]

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path in self.managed]


class ChezmoiDoctor(DataTable):
    def __init__(self):
        super().__init__()
        self.table = DataTable()
        self.lines = chezmoi.doctor()

    def create_doctor_table(self):
        self.table.add_columns(*self.lines.pop(0).split())
        rows = [row.split(maxsplit=2) for row in self.lines]

        for row in rows:
            if row[0] == "ok":
                row[0] = f"[#90EE90]{row[0]}[/]"
                row[1] = f"[#90EE90]{row[1]}[/]"
                row[2] = f"[#90EE90]{row[2]}[/]"
            if row[0] == "info":
                row[0] = f"[#E0FFFF]{row[0]}[/]"
                if row[2] == "not set":
                    row[1] = f"[#E0FFFF]{row[1]}[/]"
                    row[2] = f"[#E0FFFF]{row[2]}[/]"
                else:
                    row[1] = f"[#E0FFFF dim]{row[1]}[/]"
                    row[2] = f"[#E0FFFF dim]{row[2]}[/]"
            if row[0] == "warning":
                row[0] = f"[#FFD700]{row[0]}[/]"
                row[1] = f"[#FFD700]{row[1]}[/]"
                row[2] = f"[#FFD700]{row[2]}[/]"
            if row[0] == "error":
                row[0] = f"[red]{row[0]}[/]"
                row[1] = f"[red]{row[1]}[/]"
                row[2] = f"[red]{row[2]}[/]"

            self.table.add_row(*row)

        return self.table


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
    richlog_visible = reactive(False)

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
                "Doctor",
                "Managed",
                "Diagram",
                "Config-dump",
                "Data",
                "Config-cat",
                "Globals",
                "Locals",
                "Help",
            ):
                with VerticalScroll():
                    yield ChezmoiDoctor().create_doctor_table()
                yield ManagedFiles()
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield Pretty(CM_CONFIG_DUMP)
                with VerticalScroll():
                    yield Pretty(chezmoi.data())
                with VerticalScroll():
                    yield Pretty(chezmoi.cat_config())
                with VerticalScroll():
                    yield Pretty(self.globaldict)
                with VerticalScroll():
                    yield Pretty(locals())
                with VerticalScroll():
                    yield Static(HELP_TEXT)

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
        self.richlog_visible = not self.richlog_visible

    def watch_richlog_visible(self, richlog_visible: bool) -> None:
        # Set or unset visible class when reactive changes.
        self.query_one(RichLogSidebar).set_class(richlog_visible, "-visible")
