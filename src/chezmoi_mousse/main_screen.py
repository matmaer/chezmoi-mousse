from pathlib import Path
from collections.abc import Iterable

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.lazy import Lazy
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Collapsible,
    DataTable,
    DirectoryTree,
    Checkbox,
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
)


class GitLog(DataTable):

    def __init__(self) -> None:
        super().__init__(id="git_log", classes="margin-top-bottom")

    def on_mount(self) -> None:
        self.add_columns("COMMIT", "MESSAGE")
        git_log_output = chezmoi.git_log.std_out.splitlines()

        for line in git_log_output:
            columns = line.split(";")
            self.add_row(*columns)


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.border_title = "outputs from chezmoi commands"

    def compose(self) -> ComposeResult:

        yield VerticalScroll(
            Collapsible(
                Pretty(chezmoi.get_config_dump),
                title="chezmoi dump-config",
            ),
            Collapsible(
                Pretty(chezmoi.get_template_data),
                title="chezmoi data (template data)",
            ),
            Collapsible(
                Pretty(chezmoi.ignored.std_out.splitlines()),
                title="chezmoi ignored (git ignore in source-dir)",
            ),
            Collapsible(
                Pretty(chezmoi.cat_config.std_out.splitlines()),
                title="chezmoi cat-config (contents of config-file)",
            ),
            Collapsible(
                GitLog(),
                title="chezmoi git log (last 10 commits)",
            ),
        )


class Doctor(Static):

    output: list[str]

    class DoctorTable(DataTable):

        def __init__(self, output) -> None:
            super().__init__(id="doctor", classes="margin-top-bottom")
            self.output = output

        def on_mount(self) -> None:
            self.add_columns(*self.output.pop(0).split())

            success = self.app.current_theme.success
            warning = self.app.current_theme.warning
            error = self.app.current_theme.error

            for row in [row.split(maxsplit=2) for row in self.output]:
                if "-command" in row[1]:
                    continue
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
                self.add_row(*row)

    def __init__(self) -> None:
        super().__init__()
        self.output = chezmoi.doctor.std_out.strip().splitlines()
        self.doctor_table = self.DoctorTable(self.output)

    def compose(self) -> ComposeResult:
        yield self.doctor_table
        yield Label(
            "Local commands skipped because not in Path:",
        )
        yield DataTable(
            id="second_table",
            cursor_type="row",
            classes="margin-top-bottom",
        )

    def on_mount(self) -> None:

        second_table = self.query_one("#second_table")
        second_table.add_columns("COMMAND", "DESCRIPTION", "URL")

        for row in [row.split(maxsplit=2) for row in self.output]:
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

        chezmoi_status = chezmoi.chezmoi_status.std_out.splitlines()

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


class ManagedTree(Tree):

    def __init__(self) -> None:
        super().__init__(
            label="managed_tree",
            id="managed_tree",
            classes="margin-top-bottom",
        )
        self.show_root = False

    def on_mount(self) -> None:
        dest_dir_path = Path(chezmoi.get_config_dump["destDir"])
        dir_paths = set(p for p in chezmoi.get_managed_paths if p.is_dir())
        file_paths = set(p for p in chezmoi.get_managed_paths if p.is_file())

        def recurse_paths(parent, dir_path):
            if dir_path == dest_dir_path:
                parent = self.root
            else:
                parent = parent.add(dir_path.parts[-1], dir_path)
            files = [f for f in file_paths if f.parent == dir_path]
            for file in files:
                parent.add_leaf(str(file.parts[-1]), file)
            sub_dirs = [d for d in dir_paths if d.parent == dir_path]
            for sub_dir in sub_dirs:
                recurse_paths(parent, sub_dir)

        recurse_paths(self.root, dest_dir_path)
        self.root.expand_all()

    # def _on_tree_node_selected(self, message: Tree.NodeSelected) -> None:
    #     node_data = message.node.data
    #     managed_file = self.query_one("#managed_file_status")
    #     message.stop()


class MousseTree(DirectoryTree):  # pylint: disable=too-many-ancestors

    show_all = reactive(False)

    def __init__(self) -> None:
        super().__init__(
            path=chezmoi.get_config_dump["destDir"],
            classes="margin-top-bottom",
            id="destdirtree",
        )

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        if self.show_all:
            return paths
        return [p for p in paths if p in chezmoi.get_managed_paths]


class ManagedDirTree(Widget):

    def compose(self) -> ComposeResult:
        yield Checkbox(
            "Include Unmanaged Files",
            id="tree-checkbox",
            classes="margin-top-bottom",
        )
        yield MousseTree()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        dir_tree = self.query_one(MousseTree)
        dir_tree.show_all = event.value
        dir_tree.reload()


class MainScreen(Screen):

    BINDINGS = {
        ("i, I", "toggle_slidebar", "Toggle Inspect"),
        ("s, S", "toggle_spacing", "Toggle Spacing"),
    }

    def compose(self) -> ComposeResult:

        yield Header(classes="-tall")
        yield Lazy(SlideBar())
        with TabbedContent(
            "Managed-Tree",
            "Managed-DirTree",
            "Doctor",
            "Diagram",
            "Chezmoi-Status",
        ):
            yield VerticalScroll(Lazy(ManagedTree()))
            yield VerticalScroll(Lazy(ManagedDirTree()))
            yield VerticalScroll(Lazy(Doctor()))
            yield Lazy(Static(FLOW, id="diagram"))
            yield VerticalScroll(Lazy(ChezmoiStatus()))

        yield Footer(classes="just-margin-top")

    # Underscore to ignore return value from screen.dismiss()
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.query_one(DataTable).toggle_class("margin-top-bottom")
        self.query_one(Footer).toggle_class("just-margin-top")
        self.query_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
