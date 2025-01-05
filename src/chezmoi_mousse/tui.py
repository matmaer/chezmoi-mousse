"""Contains the Textual App class for the TUI."""

from pathlib import Path
from typing import Iterable

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    DirectoryTree,
    Footer,
    Pretty,
    RichLog,
    Static,
    TabbedContent,
)

from chezmoi_mousse import chezmoi, StdOut
from chezmoi_mousse.text_blocks import VISUAL_DIAGRAM

CM_CONFIG_DUMP = chezmoi.dump_config()


class MainMenu(Vertical):
    def compose(self) -> ComposeResult:
        yield Button(
            label="Inspect",
            id="inspect",
        )
        yield Button(
            label="Operate",
            id="operate",
        )
        yield Button(
            label="Setting",
            id="settings",
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
                row[0] = f"[#E0FFFF bold]{row[0]}[/]"
                if row[2] == "not set":
                    row[1] = f"[#E0FFFF bold]{row[1]}[/]"
                    row[2] = f"[#FFD700]{row[2]}[/]"
                else:
                    row[1] = f"[#E0FFFF bold]{row[1]}[/]"
                    row[2] = f"[#E0FFFF bold dim]{row[2]}[/]"
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
        Binding(
            key="m",
            action="toggle_mainmenu",
            description="Main Menu",
            key_display="m",
        ),
        Binding(
            key="s",
            action="toggle_stdout",
            description="Standard Output",
            key_display="s",
        ),
        # to be implemented when modal/screen/layouts are implemented
        # Binding(
        #     key="escape",
        #     action="app.pop_screen",
        #     description="Go Back",
        #     key_display="esc",
        # ),
        Binding(
            key="q",
            action="quit",
            description="Quit",
            key_display="q",
        ),
        # to be implemented when command palette is customized
        # Binding(
        #     key="h",
        #     action="help",
        #     description="Help",
        #     key_display="h",
        # ),
    ]
    CSS_PATH = "tui.tcss"
    richlog_visible = reactive(False)

    def rlog(self, to_print: str) -> None:
        richlog = self.query_one(RichLog)
        richlog.write(to_print)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield MainMenu()
            with TabbedContent(
                "Doctor",
                "Managed",
                "Diagram",
                "Config-dump",
                "Data",
                "Config-cat",
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

            yield StdOut()
        yield Footer()

    @on(Button.Pressed, "#inspect")
    def enter_inspect_mode(self):
        self.rlog("[cyan]Inspect Mode[/]")
        self.rlog("[red]Inspect mode is not yet implemented[/]")

    @on(Button.Pressed, "#operate")
    def enter_operate_mode(self):
        self.rlog("[cyan]Operate Mode[/]")
        self.rlog("[red]Operate mode is not yet implemented[/]")

    @on(Button.Pressed, "#settings")
    def enter_config_mode(self):
        self.rlog("[cyan]Configuration Mode[/]")
        self.rlog("[red]Configuration mode is not yet implemented[/]")

    def action_toggle_mainmenu(self):
        self.query_one(MainMenu).toggle_class("-hidden")

    def action_toggle_stdout(self) -> None:
        self.richlog_visible = not self.richlog_visible

    def watch_richlog_visible(self, richlog_visible: bool) -> None:
        # Set or unset visible class when reactive changes.
        self.query_one(StdOut).set_class(richlog_visible, "-visible")
