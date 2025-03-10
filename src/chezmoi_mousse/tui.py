from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import (
    Collapsible,
    DataTable,
    Footer,
    Header,
    Label,
    Pretty,
    Static,
    TabbedContent,
)

from chezmoi_mousse.common import (
    FLOW,
    chezmoi,
    integrated_command,
    oled_dark_background,
)
from chezmoi_mousse.splash import LoadingScreen


class SlideBar(Widget):

    def compose(self) -> ComposeResult:
        yield Label("Outputs from chezmoi commands:")

        yield VerticalScroll(
            Collapsible(
                Pretty(chezmoi.dump_config.py_out),
                title="chezmoi dump-config",
            ),
            Collapsible(
                Pretty(chezmoi.template_data.py_out),
                title="chezmoi data (template data)",
            ),
            Collapsible(
                Pretty(chezmoi.ignored.py_out),
                title="chezmoi ignored (git ignore in source-dir)",
            ),
            Collapsible(
                Pretty(chezmoi.cat_config.py_out),
                title="chezmoi cat-config (contents of config-file)",
            ),
            Collapsible(
                Pretty(chezmoi.git_log.py_out),
                title="chezmoi git log -- --one-line",
            ),
            Collapsible(
                Pretty(chezmoi.git_status.py_out), title="chezmoi git status"
            ),
            Collapsible(
                Pretty(chezmoi.unmanaged.py_out),
                title="chezmoi unmanaged (in destination directory)",
            ),
        )


class ChezmoiDoctor(Static):

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="main_table",
            cursor_type="row",
            classes="space",
        )
        yield Label(
            "Local commands skipped because not in Path:",
            classes="just-bold",
        )
        yield DataTable(
            id="second_table",
            cursor_type="row",
            classes="space",
        )

    def on_mount(self) -> None:

        doctor = chezmoi.doctor.py_out

        # at startup, the class gets mounted before the doctor command is run
        if chezmoi.doctor.std_out == "":
            doctor = chezmoi.doctor.updated_py_out()

        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")

        main_table.add_columns(*doctor.pop(0).split())
        second_table.add_columns("COMMAND", "DESCRIPTION", "URL")

        for row in [row.split(maxsplit=2) for row in doctor]:
            if row[0] == "info" and "not found in $PATH" in row[2]:
                # check if the command exists in the integrated_command dict
                command = row[2].split()[0]
                if command in integrated_command:
                    row = [
                        command,
                        integrated_command[command]["Description"],
                        integrated_command[command]["URL"],
                    ]
                else:
                    row = [
                        command,
                        "Not found in $PATH",
                        "...",
                    ]
                second_table.add_row(*row)
            else:
                if row[0] == "ok":
                    row = [f"[#4EBF71]{cell}[/]" for cell in row]
                elif row[0] == "warning":
                    row = [f"[#ffa62b]{cell}[/]" for cell in row]
                elif row[0] == "error":
                    row = [f"[red]{cell}[/]" for cell in row]
                elif row[0] == "info" and row[2] == "not set":
                    row = [f"[#ffa62b]{cell}[/]" for cell in row]
                else:
                    row = [f"[#ffa62b]{cell}[/]" for cell in row]
                main_table.add_row(*row)


class ChezmoiTUI(App):

    BINDINGS = {
        ("i, I", "toggle_slidebar", "Inspect"),
        ("S, s", "toggle_space", "Space"),
    }

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        yield SlideBar()
        with TabbedContent(
            "Doctor",
            "Diagram",
            "Chezmoi-Status",
        ):
            yield VerticalScroll(ChezmoiDoctor())
            yield Static(FLOW, id="diagram")
            yield Pretty(chezmoi.chezmoi_status.py_out)

        yield Footer(classes="just-margin-top")

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        # TODO: create variants for Textual Dark theme.
        self.register_theme(oled_dark_background)
        self.push_screen("loading", self.refresh_app)

    # Underscore to ignore return value from screen.dismiss()
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")

    def action_toggle_space(self):
        self.query_one(Header).toggle_class("-tall")
        self.query_one(DataTable).toggle_class("space")
        self.query_one(Footer).toggle_class("just-margin-top")

    def key_space(self) -> None:
        self.action_toggle_space()
