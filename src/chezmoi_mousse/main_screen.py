from pathlib import Path
from collections.abc import Iterable

from rich.text import Text
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
    ListItem,
    ListView,
    Pretty,
    Static,
    TabbedContent,
    Tree,
)

from chezmoi_mousse.common import FLOW, chezmoi, doctor_cmd_map


class GitLog(DataTable):

    def __init__(self) -> None:
        super().__init__(id="git_log")

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


class Doctor(Widget):

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield DataTable(id="doctor")
            yield ListView(id="cmds_not_found")

    def on_mount(self) -> None:
        doctor_data = chezmoi.get_doctor_rows
        table = self.query_one(DataTable)
        table.add_columns(*doctor_data["table_rows"][0])
        table.cursor_type = "row"

        for row in doctor_data["table_rows"][1:]:
            if row[0] == "ok":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.success}")
                    for cell in row
                ]
            elif row[0] == "warning":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.warning}")
                    for cell in row
                ]
            elif row[0] == "error":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.error}")
                    for cell in row
                ]
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(str(cell), style=f"{self.app.current_theme.warning}")
                    for cell in row
                ]
            else:
                row = [Text(str(cell)) for cell in row]
            table.add_row(*row)

        listview = self.query_one(ListView)
        for row in doctor_data["cmds_not_found"]:
            item = Collapsible(
                Pretty(row),
                title=row[1],
            )
            listview.append(ListItem(item))


class ChezmoiStatus(Static):

    def compose(self) -> ComposeResult:
        yield ListView()

    def on_mount(self):
        chezmoi_status = chezmoi.chezmoi_status.std_out.splitlines()

        listview = self.query_one(ListView)

        for line in chezmoi_status:
            item = Collapsible(
                Label("Apply Status:"),
                Static("Apply Change"),
                Label("Re-Add Status:"),
                Static("re_add_change"),
                title=line,
            )
            listview.append(ListItem(item))


class ManagedTree(Tree):

    def __init__(self) -> None:
        super().__init__(
            label="managed_tree",
            id="managed_tree",
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
            "Doctor",
            "Managed-Tree",
            "Managed-DirTree",
            "Diagram",
            "Chezmoi-Status",
        ):
            yield VerticalScroll(Lazy(Doctor()))
            yield VerticalScroll(Lazy(ManagedTree()))
            yield VerticalScroll(Lazy(ManagedDirTree()))
            yield Lazy(Static(FLOW, id="diagram"))
            yield VerticalScroll(Lazy(ChezmoiStatus()))

        yield Footer(classes="just-margin-top")

    # Underscore to ignore return value from screen.dismiss()
    def refresh_app(self, _) -> None:
        self.refresh(recompose=True)

    def action_toggle_slidebar(self):
        self.query_one(SlideBar).toggle_class("-visible")

    def action_toggle_spacing(self):
        self.query_one(Footer).toggle_class("just-margin-top")
        self.query_one(Header).toggle_class("-tall")

    def key_space(self) -> None:
        self.action_toggle_spacing()
