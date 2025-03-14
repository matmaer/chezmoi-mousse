import re
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.lazy import Lazy
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Checkbox,
    Collapsible,
    DataTable,
    DirectoryTree,
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
    chezmoi_status_map,
    integrated_command_map,
    mousse_theme,
)
from chezmoi_mousse.splash import LoadingScreen


class GitLog(Static):

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="git_log_table",
            classes="margin-top-bottom",
        )

    def parse_commit_message(self, commit_message: str) -> str:
        """Parse commit message."""
        all_git_status_words = [
            "Added",
            "Copied",
            "Deleted",
            "Modified",
            "Renamed",
            "Type-Change",
            "Unmerged",
            "Unknown",
            "Broken",
        ]

        # Create a regex pattern that matches any of the words in all_git_status_words
        pattern = r'|'.join(all_git_status_words)

        message_text = []

        lines = [line.strip() for line in commit_message.split("\n")]
        for line in lines:
            if line.split(" ")[0] not in all_git_status_words:
                message_text.append(line)
                continue
            split_by_status = re.split(pattern, line)
            if len(split_by_status) < 2:
                message_text.append(line)
                continue
            for status_line in split_by_status:
                message_text.append(status_line)
        return "\n".join(message_text)


    def on_mount(self) -> None:

        git_log_table = self.query_one("#git_log_table")
        git_log_table.add_columns("COMMIT", "MESSAGE")
        git_log_output = chezmoi.git_log.std_out.splitlines()

        for line in git_log_output:
            columns = line.split(";")
            commit_title = columns[0]
            commit_message = columns[1]
            message_column_text = self.parse_commit_message(commit_message)
            git_log_table.add_row(commit_title, message_column_text)


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.border_title = "outputs from chezmoi commands"

    def compose(self) -> ComposeResult:

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
                GitLog(),
                title="chezmoi git log (last 10 commits)",
            ),
        )


class Doctor(Static):

    def compose(self) -> ComposeResult:
        yield DataTable(
            id="main_table",
            cursor_type="row",
            classes="margin-top-bottom",
        )
        yield Label(
            "Local commands skipped because not in Path:",
        )
        yield DataTable(
            id="second_table",
            cursor_type="row",
            classes="margin-top-bottom",
        )

    def on_mount(self) -> None:

        # At startup, the class gets mounted before the doctor command is run
        # however, self.app.refresh() is called after dismissing the loading
        # screen. TODO: look into Lazy mounting and why this is still needed.
        if chezmoi.doctor.std_out == "":
            return

        main_table = self.query_one("#main_table")
        second_table = self.query_one("#second_table")
        second_table.add_columns("COMMAND", "DESCRIPTION", "URL")

        doctor = chezmoi.doctor.py_out
        main_table.add_columns(*doctor.pop(0).split())

        success = self.app.current_theme.success
        warning = self.app.current_theme.warning
        error = self.app.current_theme.error

        for row in [row.split(maxsplit=2) for row in doctor]:
            if row[0] == "info" and "not found in $PATH" in row[2]:
                # check if the command exists in the integrated_command dict
                command = row[2].split()[0]
                if command in integrated_command_map:
                    row = [
                        command,
                        integrated_command_map[command]["Description"],
                        integrated_command_map[command]["URL"],
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
                    row = [f"[{success}]{cell}[/]" for cell in row]
                elif row[0] == "warning":
                    row = [f"[{warning}]{cell}[/]" for cell in row]
                elif row[0] == "error":
                    row = [f"[{error}]{cell}[/]" for cell in row]
                elif row[0] == "info" and row[2] == "not set":
                    row = [f"[{warning}]{cell}[/]" for cell in row]
                else:
                    row = [f"[{warning}]{cell}[/]" for cell in row]
                main_table.add_row(*row)


class ChezmoiStatus(Static):

    def compose(self) -> ComposeResult:
        yield Label("Chezmoi Apply Status")
        yield DataTable(id="apply_table")
        yield Label("Chezmoi Re-Add Status")
        yield DataTable(id="re_add_table")

    def on_mount(self):
        # see comment in Doctor on_mount()
        if chezmoi.chezmoi_status.std_out == "":
            return

        chezmoi_status = chezmoi.chezmoi_status.py_out

        re_add_table = self.query_one("#re_add_table")
        apply_table = self.query_one("#apply_table")

        header_row = ["STATUS", "PATH", "CHANGE"]

        re_add_table.add_columns(*header_row)
        apply_table.add_columns(*header_row)

        for line in chezmoi_status:
            path = line[3:]

            apply_status = chezmoi_status_map[line[0]]["Status"]
            apply_change = chezmoi_status_map[line[0]]["Apply_Change"]

            re_add_status = chezmoi_status_map[line[1]]["Status"]
            re_add_change = chezmoi_status_map[line[1]]["Re_Add_Change"]

            apply_table.add_row(*[apply_status, path, apply_change])
            re_add_table.add_row(*[re_add_status, path, re_add_change])


class MousseTree(DirectoryTree):  # pylint: disable=too-many-ancestors

    show_all = reactive(False)

    def __init__(self) -> None:
        super().__init__(
            path=chezmoi.dest_dir,
            classes="margin-top-bottom",
            id="destdirtree",
        )

    def filter_paths(self, paths: list[str]) -> list[str]:
        if self.show_all:
            return chezmoi.managed_paths + chezmoi.unmanaged_paths
        return [p for p in paths if p in chezmoi.managed_paths]


class ManagedTree(Widget):

    def compose(self) -> ComposeResult:
        yield Checkbox(
            "Include Unmanaged Files",
            id="tree-checkbox",
            classes="just-margin-top",
        )
        yield MousseTree()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        dir_tree = self.query_one(MousseTree)
        dir_tree.show_all = event.value
        dir_tree.reload()


class ChezmoiTUI(App):

    BINDINGS = {
        ("i, I", "toggle_slidebar", "Toggle Inspect"),
        ("s, S", "toggle_spacing", "Toggle Spacing"),
    }

    CSS_PATH = "tui.tcss"

    SCREENS = {
        "loading": LoadingScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header(classes="-tall")
        yield Lazy(SlideBar())
        with TabbedContent(
            "destDir-Tree",
            "Doctor",
            "Diagram",
            "Chezmoi-Status",
        ):
            yield VerticalScroll(ManagedTree())
            yield VerticalScroll(Lazy(Doctor()))
            yield Lazy(Static(FLOW, id="diagram"))
            yield VerticalScroll(Lazy(ChezmoiStatus()))

        yield Footer(classes="just-margin-top")

    @work
    async def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        self.register_theme(mousse_theme)
        self.theme = "mousse-theme"
        self.push_screen("loading", self.refresh_app)

    # Underscore to ignore return value from screen.dismiss()
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.query_one(Checkbox).toggle_class("just-margin-top")
        self.query_one(DataTable).toggle_class("margin-top-bottom")
        self.query_one(DirectoryTree).toggle_class("margin-top-bottom")
        self.query_one(Footer).toggle_class("just-margin-top")
        self.query_one(GitLog).toggle_class("margin-top-bottom")
        self.query_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
