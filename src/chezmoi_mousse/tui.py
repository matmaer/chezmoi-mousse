from pathlib import Path
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.lazy import Lazy
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
    Tree,
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

    def on_mount(self) -> None:

        git_log_table = self.query_one("#git_log_table")
        git_log_table.add_columns("COMMIT", "MESSAGE")
        git_log_output = chezmoi.git_log.std_out.splitlines()

        for line in git_log_output:
            columns = line.split(";")
            git_log_table.add_row(*columns)


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


class ManagedTree(Static):

    def compose(self) -> ComposeResult:
        yield Tree(label=chezmoi.dest_dir, id="managed_tree")

    def on_mount(self) -> None:

        managed_tree = self.query_one("#managed_tree")
        managed_paths = chezmoi.get_managed_paths()
        managed_dirs = [p for p in managed_paths if p.is_dir()]

        def create_recursive(subdir_paths: list[Path], parent_node):
            # Group paths by their first part
            grouped_paths = {}
            for path in subdir_paths:
                root = path.parts[0]
                if root not in grouped_paths:
                    grouped_paths[root] = []
                grouped_paths[root].append(path.relative_to(root))

            # Add each group to the parent node and recurse
            for root, paths in grouped_paths.items():
                child_node = parent_node.add(root)
                create_recursive([p for p in paths if p.parts], child_node)

        # Start the recursive creation from the root node
        managed_dirs = [p.relative_to(chezmoi.dest_dir) for p in managed_dirs]
        create_recursive(managed_dirs, managed_tree.root)


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
            "Managed-Tree",
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
        self.query_one(DataTable).toggle_class("margin-top-bottom")
        self.query_one(Footer).toggle_class("just-margin-top")
        self.query_one(GitLog).toggle_class("margin-top-bottom")
        self.query_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
