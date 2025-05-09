"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    VerticalGroup,
    VerticalScroll,
)
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
    ApplyTree,
    AutoWarning,
    ChezmoiStatus,
    FileViewCollapsible,
    FilteredDirTree,
    ReactiveFileView,
    ReAddTree,
    SlideBar,
)
from chezmoi_mousse.config import pw_mgr_info


class AddTab(Container):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "add_path", "Add Path"),
    ]

    def __init__(self) -> None:
        self.filter_switches: list[HorizontalGroup] = []
        super().__init__(id="add_tab")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FilteredDirTree(
                dest_dir, classes="dir-tree any-tree", id="filtered_dir_tree"
            )
            yield ReactiveFileView()
        yield SlideBar(filter_key="add_tab", tab_filters_id="add_filters")

    def on_mount(self) -> None:
        dir_tree = self.query_one("#filtered_dir_tree", FilteredDirTree)
        dir_tree.show_root = False
        dir_tree.border_title = f" {dest_dir} "

    @on(FilteredDirTree.FileSelected)
    def update_preview_path(self, event: FilteredDirTree.FileSelected) -> None:
        self.query_exactly_one(ReactiveFileView).file_path = event.path

    def action_toggle_slidebar(self):
        self.screen.query_one("#add_filters", SlideBar).toggle_class(
            "-visible"
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.query_one("#filtered_dir_tree", FilteredDirTree)
        if event.switch.id == "add_tab_unmanaged":
            add_dir_tree.include_unmanaged_dirs = event.value
            add_dir_tree.reload()
        elif event.switch.id == "add_tab_unwanted":
            add_dir_tree.filter_unwanted = event.value
            add_dir_tree.reload()

    def action_add_path(self) -> None:
        cursor_node = self.query_one(
            "#filtered_dir_tree", FilteredDirTree
        ).cursor_node
        self.app.push_screen(ChezmoiAdd(cursor_node.data.path))  # type: ignore[reportOptionalMemberAccess] # pylint: disable=line-too-long

    def on_resize(self) -> None:
        self.query_one("#filtered_dir_tree", FilteredDirTree).focus()


class ChezmoiAdd(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss", "dismiss modal screen", show=False)
    ]

    def __init__(self, path_to_add: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path_to_add = path_to_add
        self.files_to_add: list[Path] = []
        self.add_path_items: list[FileViewCollapsible] = []

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield AutoWarning()
            yield from self.add_path_items
            yield Horizontal(
                Button(
                    "- Add File -", id="addfile", classes="add-modal-button"
                ),
                Button(
                    "- Cancel -", id="canceladding", classes="add-modal-button"
                ),
                id="button_container",
            )

    def on_mount(self) -> None:
        self.files_to_add: list[Path] = []
        if self.path_to_add.is_file():
            self.files_to_add: list[Path] = [self.path_to_add]
        elif self.path_to_add.is_dir():
            self.files_to_add = [
                f for f in chezmoi.unmanaged_in_d(self.path_to_add)
            ]
        if len(self.files_to_add) == 0:
            self.notify(
                f"The selected directory does not contain unmanaged files to add.\nDirectory: {self.path_to_add}."
            )
            self.dismiss()
        elif len(self.files_to_add) > 1:
            self.add_label = "- Add Files -"

        for f in self.files_to_add:
            self.add_path_items.append(FileViewCollapsible(file_path=f))
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


class PrettyModal(ModalScreen):

    BINDINGS = [Binding("escape", "dismiss", "", show=True)]

    def __init__(self, pretty_object: Pretty | DataTable) -> None:
        self.pretty_object = pretty_object
        super().__init__(classes="modalscreen")

    def compose(self) -> ComposeResult:
        yield self.pretty_object


class DoctorTab(VerticalScroll):

    BINDINGS = [
        Binding("c", "open_config", "dump-config"),
        Binding("g", "git_log", "git-log"),
    ]

    def __init__(self) -> None:
        self.git_log = DataTable(
            id="gitlog", classes="doctortable", show_cursor=False
        )
        super().__init__()

    def compose(self) -> ComposeResult:

        yield DataTable(
            id="doctortable", classes="doctortable", show_cursor=False
        )
        with VerticalGroup(classes="collapsiblegroup"):
            yield Collapsible(
                ListView(id="cmdnotfound"), title="Commands Not Found"
            )
            yield Collapsible(
                Pretty(chezmoi.template_data.dict_out),
                title="chezmoi data (template data)",
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

        self.git_log.add_columns("COMMIT", "MESSAGE")
        for line in chezmoi.git_log.list_out:
            columns = line.split(";")
            if columns[1].split(maxsplit=1)[0] == "Add":
                row = [
                    Text(cell_text, style=f"{styles["ok"]}")
                    for cell_text in columns
                ]
                self.git_log.add_row(*row)
            elif columns[1].split(maxsplit=1)[0] == "Update":
                row = [
                    Text(cell_text, style=f"{styles["warning"]}")
                    for cell_text in columns
                ]
                self.git_log.add_row(*row)
            elif columns[1].split(maxsplit=1)[0] == "Remove":
                row = [
                    Text(cell_text, style=f"{styles["error"]}")
                    for cell_text in columns
                ]
                self.git_log.add_row(*row)
            else:
                self.git_log.add_row(*columns)

    def action_open_config(self) -> None:
        self.app.push_screen(PrettyModal(Pretty(chezmoi.dump_config.dict_out)))

    def action_git_log(self) -> None:
        self.app.push_screen(PrettyModal(self.git_log))


class ApplyTab(VerticalScroll):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "apply_path", "Apply Path"),
    ]

    def __init__(self) -> None:
        super().__init__(id="apply_tab")

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield ChezmoiStatus(apply=True)
            yield Horizontal(ApplyTree(), ReactiveFileView(id="apply_file"))
        yield SlideBar(filter_key="apply_tab", tab_filters_id="apply_filters")

    def action_toggle_slidebar(self):
        self.query_one("#apply_filters", SlideBar).toggle_class("-visible")

    def action_apply_path(self) -> None:
        self.notify("will apply path")

    def on_resize(self) -> None:
        self.query_exactly_one(ApplyTree).focus()

    @on(ApplyTree.NodeSelected)
    def update_preview_path(self, event: ApplyTree.NodeSelected) -> None:
        self.query_exactly_one(ReactiveFileView).file_path = event.node.data

    def on_switch_changed(self, event: Switch.Changed) -> None:
        apply_tree = self.query_exactly_one(ApplyTree)
        if event.switch.id == "apply_tab_missing":
            apply_tree.missing = event.value
        elif event.switch.id == "apply_tab_changed_files":
            apply_tree.changed_files = event.value


class ReAddTab(VerticalScroll):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "re_add_path", "Re-Add Path"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield ChezmoiStatus(apply=False)
            yield Horizontal(ReAddTree(), ReactiveFileView())

        yield SlideBar(
            filter_key="re_add_tab", tab_filters_id="re_add_filters"
        )

    def action_toggle_slidebar(self):
        self.query_one("#re_add_filters", SlideBar).toggle_class("-visible")

    def action_re_add_path(self) -> None:
        self.notify("will re-add path")

    def on_resize(self) -> None:
        self.query_exactly_one(ReAddTree).focus()

    @on(ReAddTree.NodeSelected)
    def update_preview_path(self, event: ReAddTree.NodeSelected) -> None:
        self.query_exactly_one(ReactiveFileView).file_path = event.node.data

    def on_switch_changed(self, event: Switch.Changed) -> None:
        re_add_tree = self.query_exactly_one(ReAddTree)
        if event.switch.id == "re_add_tab_changed_files":
            re_add_tree.changed_files = event.value


class DiagramTab(VerticalScroll):

    def compose(self) -> ComposeResult:
        yield Static(FLOW, id="diagram")
