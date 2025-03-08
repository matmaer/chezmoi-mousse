from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
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

from chezmoi_mousse.common import FLOW, chezmoi, oled_dark_zen
from chezmoi_mousse.splash import LoadingScreen


class SlideBar(Widget):

    # def __init__(self, highlight: bool = False):
    #     super().__init__()
    #     self.animate = True
    #     self.auto_scroll = True
    #     self.highlight = highlight
    #     self.id = "slidebar"
    #     self.markup = True
    #     self.max_lines = 160  # (80×3÷2)×((16−4)÷9)
    #     self.wrap = True

    def compose(self) -> ComposeResult:
        yield Label("Outputs from chezmoi commands:")
        with Collapsible(title="chezmoi dump-config"):
            yield VerticalScroll(Pretty(chezmoi.dump_config.py_out))
        with Collapsible(title="chezmoi data (template data)"):
            yield VerticalScroll(Pretty(chezmoi.template_data.py_out))
        with Collapsible(title="chezmoi ignored (git ignore in source-dir)"):
            yield VerticalScroll(Pretty(chezmoi.ignored.py_out))
        with Collapsible(title="chezmoi cat-config (contents of config-file)"):
            yield VerticalScroll(Pretty(chezmoi.cat_config.py_out))



class ChezmoiDoctor(Static):

    # pylint: disable=line-too-long
    command_info = {
        "age": {
            "Description": "A simple, modern and secure file encryption tool",
            "URL": "https://github.com/FiloSottile/age",
        },
        "gopass": {
            "Description": "The slightly more awesome standard unix password manager for teams.",
            "URL": "https://github.com/gopasspw/gopass",
        },
        "pass": {
            "Description": "Stores, retrieves, generates, and synchronizes passwords securely",
            "URL": "https://www.passwordstore.org/",
        },
        "rbw": {
            "Description": "Unofficial Bitwarden CLI",
            "URL": "https://git.tozt.net/rbw",
        },
        "vault": {
            "Description": "A tool for managing secrets",
            "URL": "https://vaultproject.io/",
        },
        "pinentry": {
            "Description": "Collection of simple PIN or passphrase entry dialogs which utilize the Assuan protocol",
            "URL": "https://gnupg.org/related_software/pinentry/",
        },
        "keepassxc": {
            "Description": "Cross-platform community-driven port of Keepass password manager",
            "URL": "https://keepassxc.org/",
        },
    }

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="main_table",
            cursor_type="row",
        )
        yield Label(
            "Local commands skipped because not in Path:",
        )
        yield DataTable(
            id="second_table",
            cursor_type="row",
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
                # check if the command exists in the command_info dict
                command = row[2].split()[0]
                if command in self.command_info:
                    row = [
                        command,
                        self.command_info[command]["Description"],
                        self.command_info[command]["URL"],
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

    BINDINGS = {("i, I", "toggle_slidebar", "Inspect")}

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    show_sidebar = reactive(True)

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        yield SlideBar()
        with TabbedContent(
            # "Managed-Files",
            "Doctor",
            "Diagram",
            "Chezmoi-Status",
            "Unmanaged",
            "Git-Log",
            "Git-Status",
        ):
            # yield ManagedFiles(chezmoi.dest_dir)
            yield VerticalScroll(ChezmoiDoctor())
            yield Static(FLOW, id="diagram")
            yield Pretty(chezmoi.chezmoi_status.py_out)
            yield Pretty(chezmoi.unmanaged.py_out)
            yield Pretty(chezmoi.git_log.py_out)
            yield Pretty(chezmoi.git_status.py_out)

        yield Footer()

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(oled_dark_zen)
        # self.theme = "oled-dark-zen" # let's use textual and prioritize the
        # release of the app
        self.push_screen("loading", self.refresh_app)

    # Screen dismiss from the loading screen, returns something, so adding an
    # underscore to avoid exception saying refresh_app takes only one argument.
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")
