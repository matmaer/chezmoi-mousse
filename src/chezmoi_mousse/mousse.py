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
    ScrollableContainer,
    VerticalGroup,
    VerticalScroll,
)
from textual.reactive import reactive
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
    FileViewCollapsible,
    FilteredDirTree,
    ManagedTree,
    ReactiveFileView,
)
from chezmoi_mousse.config import pw_mgr_info


class SlideBar(VerticalGroup):

    switches_by_tab: dict[str, list[HorizontalGroup]] | None = None

    def __init__(self, filter_key: str = "apply_tab", **kwargs) -> None:
        self.filter_key = filter_key
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        if self.switches_by_tab is not None:
            yield from self.switches_by_tab[f"{self.filter_key}"]


class AddTab(Container):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "add_path", "Add Path"),
    ]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            ScrollableContainer(
                FilteredDirTree(dest_dir, classes="dir-tree"),
                classes="scrollable-dir-tree",
            ),
            ReactiveFileView(classes="file-preview"),
        )
        yield SlideBar(filter_key="add_tab", id="add_filters")

    @on(FilteredDirTree.FileSelected)
    def update_preview_path(self, event: FilteredDirTree.FileSelected) -> None:
        self.query_one(ReactiveFileView).file_path = event.path

    def action_toggle_slidebar(self):
        self.screen.query_one("#add_filters").toggle_class("-visible")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.screen.query_exactly_one(FilteredDirTree)
        if event.switch.id == "unmanaged":
            add_dir_tree.include_unmanaged_dirs = event.value
            add_dir_tree.reload()
        elif event.switch.id == "unwanted":
            add_dir_tree.filter_unwanted = event.value
            add_dir_tree.reload()

    def action_add_path(self) -> None:
        cursor_node = self.query_exactly_one(FilteredDirTree).cursor_node
        self.app.push_screen(ChezmoiAdd(cursor_node.data.path))  # type: ignore[reportOptionalMemberAccess] # pylint: disable=line-too-long

    def on_resize(self) -> None:
        self.query_one(FilteredDirTree).focus()


class ChezmoiAdd(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss", "dismiss modal screen", show=False)
    ]

    def __init__(self, path_to_add: Path) -> None:
        super().__init__()
        self.path_to_add = path_to_add
        self.files_to_add: list[Path] = []
        self.add_path_items: list[FileViewCollapsible] = []
        self.add_label = "- Add File -"

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modalscreen"):
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
                # TODO: implement checkbokes for files to add and take into account the filters for the directory tree selected by the user, so only the displayed children are shown on the modal
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

    filter_switches = "apply_tab"  # Use the filter group name defined in SlideBar.FILTER_GROUPS

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "apply_path", "Apply Path"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield ChezmoiStatus(apply=True)
            yield Horizontal(
                ScrollableContainer(
                    ManagedTree(id="apply_tree"), classes="scrollable-dir-tree"
                ),
                ReactiveFileView(classes="file-preview"),
            )
        yield SlideBar(filter_key="apply_tab", id="apply_filters")

    @on(ManagedTree.NodeSelected)
    def update_preview_path(self, event: ManagedTree.NodeSelected) -> None:
        if event.node.data is not None and event.node.data.is_file():
            self.query_one(ReactiveFileView).file_path = event.node.data
        elif (
            event.node.data is not None
            and not event.node.data.is_dir()
            and not event.node.data.exists()
        ):
            self.query_one(ReactiveFileView).file_path = event.node.data

    def action_toggle_slidebar(self):
        self.screen.query_one("#apply_filters").toggle_class("-visible")

    def action_apply_path(self) -> None:
        self.notify("will apply path")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        managed_tree = self.query_exactly_one("#apply_tree")
        if event.switch.id == "not_existing":
            # filter logic here
            self.notify(f"Not yet implemented for {managed_tree}")
            managed_tree.refresh()
        elif event.switch.id == "changed_files":
            # filter logic here
            self.notify(f"Not yet implemented {managed_tree}")
            managed_tree.refresh()

    def on_resize(self) -> None:
        self.query_exactly_one(ManagedTree).focus()


class ReAddTab(VerticalScroll):

    filter_switches = "re_add_tab"  # Use the filter group name defined in SlideBar.FILTER_GROUPS

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "re_add_path", "Re-Add Path"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield ChezmoiStatus(apply=False)
            yield Horizontal(
                ScrollableContainer(
                    ManagedTree(id="re_add_tree"),
                    classes="scrollable-dir-tree",
                ),
                ReactiveFileView(classes="file-preview"),
            )

        yield SlideBar(filter_key="re_add_tab", id="re_add_filters")

    @on(ManagedTree.NodeSelected)
    def update_preview_path(self, event: ManagedTree.NodeSelected) -> None:
        if event.node.data is not None and event.node.data.is_file():
            self.query_one(ReactiveFileView).file_path = event.node.data
        elif (
            event.node.data is not None
            and not event.node.data.is_dir()
            and not event.node.data.exists()
        ):
            self.query_one(ReactiveFileView).file_path = event.node.data

    def action_toggle_slidebar(self):
        self.screen.query_one("#re_add_filters").toggle_class("-visible")

    def action_re_add_path(self) -> None:
        self.notify("will re-add path")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        managed_tree = self.query_exactly_one("#re_add_tree")
        if event.switch.id == "changed_files":
            # filter logic here
            self.notify(f"Not yet implemented for {managed_tree}")


class DiagramTab(VerticalScroll):

    def compose(self) -> ComposeResult:
        yield Static(FLOW, id="diagram")
