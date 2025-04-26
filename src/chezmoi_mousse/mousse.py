"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalGroup, VerticalScroll
from textual.lazy import Lazy
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Label,
    Link,
    ListItem,
    ListView,
    Pretty,
    Static,
    Switch,
)

from chezmoi_mousse import FLOW
from chezmoi_mousse.chezmoi import chezmoi, dest_dir
from chezmoi_mousse.components import (
    AutoWarning,
    ChezmoiStatus,
    ColoredFileContent,
    FilteredAddDirTree,
    ManagedTree,
    SlideBar,
    is_reasonable_dotfile,
)
from chezmoi_mousse.config import pw_mgr_info


class AddDirTreeTab(VerticalScroll):

    filter_switches = {
        "unmanaged": {
            "switch_label": "Include unmanaged directories",
            "switch_tooltip": "Enable to include all un-managed files, even if they live in an un-managed directory. Disable to only show un-managed files in directories which already contain managed files (the default). The purpose is to easily spot new un-managed files in already managed directories. (in both cases, only the un-managed files are shown)",
            "switch_state": False,
        },
        "unwanted": {
            "switch_label": "Filter unwanted paths",
            "switch_tooltip": 'Filter out files and directories considered as "unwanted" for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories.  You can disable this, for example if you want to add files to your chezmoi repository which are in a directory named "cache".',
            "switch_state": True,
        },
    }

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "add_path", "Add Path"),
    ]

    def compose(self) -> ComposeResult:
        yield FilteredAddDirTree(dest_dir, classes="dir-tree")
        yield SlideBar(self.filter_switches, id="addslidebar")

    def action_toggle_slidebar(self):
        self.screen.query_one("#addslidebar").toggle_class("-visible")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.screen.query_exactly_one(FilteredAddDirTree)
        if event.switch.id == "unmanaged":
            add_dir_tree.include_unmanaged_dirs = event.value
            add_dir_tree.reload()
        elif event.switch.id == "unwanted":
            add_dir_tree.filter_unwanted = event.value
            add_dir_tree.reload()

    def action_add_path(self) -> None:
        cursor_node = self.query_exactly_one(FilteredAddDirTree).cursor_node
        self.app.push_screen(ChezmoiAdd(cursor_node.data.path))  # type: ignore[reportOptionalMemberAccess] # pylint: disable:line-too-long


class ChezmoiAdd(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss", "dismiss modal screen", show=False)
    ]

    def __init__(self, path_to_add: Path) -> None:
        super().__init__()
        self.path_to_add = path_to_add
        self.files_to_add: list[Path] = []
        self.add_path_items: list[ColoredFileContent] = []
        self.add_label = "- Add File -"

    def compose(self) -> ComposeResult:
        with VerticalScroll(
            id="addfilemodalcontainer", classes="operationmodal"
        ):
            yield AutoWarning()
            with VerticalGroup(classes="collapsiblegroup"):
                yield from self.add_path_items
            yield Horizontal(
                Button(self.add_label, id="addfile"),
                Button("- Cancel -", id="canceladding"),
            )

    def on_mount(self) -> None:
        self.files_to_add: list[Path] = []
        if self.path_to_add.is_file():
            self.files_to_add: list[Path] = [self.path_to_add]
        elif self.path_to_add.is_dir():
            self.files_to_add = [
                f
                for f in chezmoi.unmanaged_in_d(self.path_to_add)
                if is_reasonable_dotfile(f)
            ]
        if len(self.files_to_add) == 0:
            # pylint: disable=line-too-long
            self.notify(
                f"The selected directory does not contain unmanaged files to add.\nDirectory: {self.path_to_add}."
            )
            self.dismiss()
        elif len(self.files_to_add) > 1:
            self.add_label = "- Add Files -"

        for f in self.files_to_add:
            self.add_path_items.append(ColoredFileContent(file_path=f))
        self.refresh(recompose=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "addfile":
            for f in self.files_to_add:
                chezmoi.add(f)
                self.notify(f"Added {f} to chezmoi.")
            self.screen.dismiss()
        elif event.button.id == "canceladding":
            self.notify("No files were added.")
            self.screen.dismiss()


class DoctorTab(VerticalScroll):

    def compose(self) -> ComposeResult:

        yield DataTable(id="doctortable", show_cursor=False)
        with VerticalGroup(classes="collapsiblegroup"):
            yield Collapsible(
                Pretty(chezmoi.dump_config.dict_out),
                title="output from 'chezmoi dump-config'",
            )
            yield Collapsible(
                ListView(id="cmdnotfound"), title="Commands Not Found"
            )
            yield Collapsible(
                Pretty(chezmoi.template_data.dict_out),
                title="chezmoi data (template data)",
            )
            yield Collapsible(
                DataTable(id="gitlog", cursor_type="row"),
                title="chezmoi git log (last 20 commits)",
            )
            yield Collapsible(
                Pretty(chezmoi.cat_config.list_out),
                title="chezmoi cat-config (contents of config-file)",
            )
            yield Collapsible(
                Pretty(chezmoi.ignored.list_out),
                title="chezmoi ignored (git ignore in source-dir)",
            )

    def on_mount(self) -> None:

        git_log_table = self.query_exactly_one("#gitlog", DataTable)
        git_log_table.add_columns("COMMIT", "MESSAGE")
        for line in chezmoi.git_log.list_out:
            columns = line.split(";")
            git_log_table.add_row(*columns)

        styles = {
            "ok": f"{self.app.current_theme.success}",
            "warning": f"{self.app.current_theme.warning}",
            "error": f"{self.app.current_theme.error}",
            "info": f"{self.app.current_theme.foreground}",
        }

        list_view = self.query_one("#cmdnotfound", ListView)
        table = self.query_one("#doctortable", DataTable)
        doctor_rows = chezmoi.doctor.list_out
        table.add_columns(*doctor_rows[0].split())

        for line in doctor_rows[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                if row[1] in pw_mgr_info:
                    list_view.append(
                        ListItem(
                            Link(row[1], url=pw_mgr_info[row[1]]["link"]),
                            Static(pw_mgr_info[row[1]]["description"]),
                        )
                    )
                elif row[1] not in pw_mgr_info:
                    list_view.append(
                        ListItem(
                            # color accent as that's how links are styled by default
                            Static(f"[$accent-muted]{row[1]}[/]", markup=True),
                            Label(
                                "Not Found in $PATH, no description available in TUI."
                            ),
                        )
                    )
            elif row[0] == "ok" or row[0] == "warning" or row[0] == "error":
                row = [
                    Text(cell_text, style=f"{styles[row[0]]}")
                    for cell_text in row
                ]
                table.add_row(*row)
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(cell_text, style=f"{self.app.current_theme.warning}")
                    for cell_text in row
                ]
                table.add_row(*row)
            else:
                row = [Text(cell_text) for cell_text in row]
                table.add_row(*row)


class ApplyTab(VerticalScroll):

    filter_switches = {
        "notexisting": {
            "switch_label": "Show only non-existing files",
            "switch_tooltip": "Show only non-existing files",
            "switch_state": False,
        },
        "changedfiles": {
            "switch_label": "Show only files with changed status",
            "switch_tooltip": "Show only files with changed status",
            "switch_state": False,
        },
    }

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "apply_path", "Apply Path"),
    ]

    def compose(self) -> ComposeResult:
        yield ChezmoiStatus(apply=True)
        yield ManagedTree(label=str("root_node"), id="applytree")
        yield SlideBar(self.filter_switches, id="applyslidebar")

    def action_toggle_slidebar(self):
        self.screen.query_exactly_one("#applyslidebar").toggle_class(
            "-visible"
        )

    def action_apply_path(self) -> None:
        self.notify("will apply path")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        managed_tree = self.query_exactly_one("#applytree")
        if event.switch.id == "notexisting":
            # filter logic here
            managed_tree.refresh()
        elif event.switch.id == "changedfiles":
            # filter logic here
            managed_tree.refresh()


class ReAddTab(VerticalScroll):

    filter_switches = {
        "changedfiles": {
            "switch_label": "Show only files with changed status",
            "switch_tooltip": "Show only files with changed status",
            "switch_state": False,
        }
    }

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "re_add_path", "Re-Add Path"),
    ]

    def compose(self) -> ComposeResult:
        yield ChezmoiStatus(apply=False)
        yield ManagedTree(
            label=str("root_node"), show_existing_only=True, id="re_add_tree"
        )

    def action_toggle_slidebar(self):
        self.screen.query_exactly_one("#applyslidebar").toggle_class(
            "-visible"
        )

    def action_re_add_path(self) -> None:
        self.notify("will re-add path")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        managed_tree = self.query_exactly_one("#applytree")
        if event.switch.id == "changedfiles":
            # filter logic here
            managed_tree.refresh()


class DiagramTab(VerticalScroll):

    def compose(self) -> ComposeResult:
        yield Static(FLOW, id="diagram")
