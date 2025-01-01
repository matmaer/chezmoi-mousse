""" Contains the Textual App class for the TUI. """

from textual import on
from textual.app import App, ComposeResult, Widget
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (Button, DirectoryTree, Footer, Header, Label,
                             Pretty, RichLog, Static, TabbedContent)

from chezmoi_mousse import CM_CONFIG_CAT, CM_CONFIG_DUMP, CM_DATA, CM_DOCTOR
from chezmoi_mousse.blocks import VISUAL_DIAGRAM


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


# class ManagedFiles(DirectoryTree):
#     def __init__(self):
#         super().__init__(Path(CHEZMOI_CONFIG["destDir"]))
#         self.to_filter = []
#         self.filtered_paths = []

#     def get_chezmoi_managed(self):
#         chezmoi_arguments = [
#             "managed",
#             "--exclude=dirs",
#             "--path-style=absolute",
#             ]
#         cm_managed = run_chezmoi(chezmoi_arguments).stdout.splitlines()
#         self.to_filter = [Path(p) for p in cm_managed]

#     def filter_paths(self):
#         for path in self.to_filter:
#             if path.name in self.to_filter:
#                 self.filtered_paths.append(path)
#         return self.filtered_paths


class ChezmoiTUI(App):
    BINDINGS = [
        ("m", "toggle_mainmenu", "Toggle Menu"),
        ("s", "toggle_richlogsidebar", "Toggle Stdout"),
        ("q", "quit", "Quit"),
    ]
    CSS_PATH = "tui.tcss"
    show_richlog = reactive(False)

    def rlog(self, to_print: str) -> None:
        richlog = self.query_one(RichLog)
        richlog.write(to_print)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield MainMenu()
            with TabbedContent(
                "Destination",
                "Diagram",
                "Doctor",
                "Config-cat",
                "Config-dump",
                "Data",
                "Globals",
                "Locals",
            ):
                yield DirectoryTree(CM_CONFIG_DUMP["destDir"])
                yield Static(VISUAL_DIAGRAM)
                with VerticalScroll():
                    yield Pretty(CM_DOCTOR)
                with VerticalScroll():
                    yield Pretty(CM_CONFIG_CAT)
                with VerticalScroll():
                    yield Pretty(CM_CONFIG_DUMP)
                with VerticalScroll():
                    yield Pretty(CM_DATA)
                with VerticalScroll():
                    yield Pretty(globals())
                with VerticalScroll():
                    yield Pretty(locals())

            yield RichLogSidebar()
        yield Footer()

        # yield Button(
        #     label="Show Stdout",
        #     id="show_stdout",
        # )
        # yield Button(
        #     label="Help",
        #     id="app_help",
        # )
        # yield Button(
        #     label="Exit",
        #     id="clean_exit",
        # )

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
