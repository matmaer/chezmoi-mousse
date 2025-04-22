"""Contains the widgets used to compose the main screen of chezmoi-mousse."""

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    VerticalGroup,
    VerticalScroll,
)
from textual.content import Content
from textual.screen import ModalScreen
from textual.widget import Widget
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

from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.components import (
    ColoredDiff,
    ColoredFileContent,
    FilteredAddDirTree,
    ManagedTree,
)
from chezmoi_mousse.config import pw_mgr_info


class AddDirTree(Widget):

    BINDINGS = [
        Binding("f", "toggle_slidebar", "Filters"),
        Binding("a", "add_path", "Add Path"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield FilteredAddDirTree(
                chezmoi.dump_config.dict_out["destDir"],
                id="adddirtree",
                classes="dir-tree",
            )

    def on_mount(self) -> None:
        self.query_one(FilteredAddDirTree).root.label = (
            f"{chezmoi.dump_config.dict_out['destDir']} (destDir)"
        )

    def action_add_path(self) -> None:
        cursor_node = self.query_exactly_one(FilteredAddDirTree).cursor_node
        self.app.push_screen(ChezmoiAdd(cursor_node.data.path))  # type: ignore[reportOptionalMemberAccess] # pylint: disable:line-too-long


class ApplyTree(ManagedTree):
    def __init__(self) -> None:
        super().__init__(label=str("root_node"), id="apply_tree")


class ChezmoiAdd(ModalScreen):

    BINDINGS = [
        Binding("escape", "dismiss", "dismiss modal screen", show=False)
    ]

    def __init__(self, path_to_add: Path) -> None:
        self.path_to_add = path_to_add
        self.files_to_add: list[Path] = []
        self.add_path_items: list[ColoredFileContent] = []
        self.add_label = "- Add File -"
        self.auto_warning = ""
        super().__init__(id="addfilemodal")

    def compose(self) -> ComposeResult:
        with Container(id="addfilemodalcontainer", classes="operationmodal"):
            if chezmoi.autocommit_enabled:
                yield Static(
                    Content.from_markup(
                        f"[$warning italic]{self.auto_warning}[/]"
                    ),
                    classes="autowarning",
                )
            yield VerticalGroup(*self.add_path_items)
            yield Horizontal(
                Button(self.add_label, id="addfile"),
                Button("- Cancel -", id="canceladding"),
            )

    def on_mount(self) -> None:
        # pylint: disable=line-too-long
        if chezmoi.autocommit_enabled and not chezmoi.autopush_enabled:
            self.auto_warning = '"Auto Commit" is enabled: added file(s) will also be committed.'
        elif chezmoi.autocommit_enabled and chezmoi.autopush_enabled:
            self.auto_warning = '"Auto Commit" and "Auto Push" are enabled: adding file(s) will also be committed and pushed the remote.'
        collapse = True
        self.files_to_add: list[Path] = []
        if self.path_to_add.is_file():
            self.files_to_add: list[Path] = [self.path_to_add]
            collapse = False
        elif self.path_to_add.is_dir():
            self.files_to_add = chezmoi.unmanaged_in_d(self.path_to_add)
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


class ChezmoiStatus(VerticalGroup):

    def __init__(self, apply: bool) -> None:
        # if true, adds apply status to the list, otherwise "re-add" status
        self.apply = apply
        self.status_items: list[ColoredDiff] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalGroup(*self.status_items)

    def on_mount(self) -> None:

        changes: list[tuple[str, Path]] = chezmoi.get_status(
            apply=self.apply, files=True, dirs=False
        )

        for status_code, path in changes:
            self.status_items.append(
                ColoredDiff(
                    file_path=path, apply=self.apply, status_code=status_code
                )
            )
        self.refresh(recompose=True)


class Doctor(Widget):

    def compose(self) -> ComposeResult:
        yield DataTable(id="doctortable", show_cursor=False)
        yield Collapsible(
            ListView(id="cmdnotfound"), title="Commands Not Found"
        )
        yield Collapsible(
            VerticalScroll(Pretty(chezmoi.dump_config.dict_out)),
            title="chezmoi dump-config",
        )
        yield Collapsible(
            VerticalScroll(Pretty(chezmoi.template_data.dict_out)),
            title="chezmoi data (template data)",
        )
        yield Collapsible(
            DataTable(id="gitlog", cursor_type="row"),
            title="chezmoi git log (last 20 commits)",
        )
        yield Collapsible(
            VerticalScroll(Pretty(chezmoi.cat_config.list_out)),
            title="chezmoi cat-config (contents of config-file)",
        )
        yield Collapsible(
            VerticalScroll(Pretty(chezmoi.ignored.list_out)),
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

        list_view = self.query_exactly_one("#cmdnotfound", ListView)
        table = self.query_exactly_one("#doctortable", DataTable)
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


class ReAddTree(ManagedTree):
    def __init__(self) -> None:
        super().__init__(
            label=str("root_node"), id="re_add_tree", show_existing_only=True
        )


class SlideBar(Widget):

    def __init__(self) -> None:
        super().__init__()
        # pylint: disable=line-too-long
        self.border_title = "filters "
        self.unmanaged_tooltip = "Enable to include all un-managed files, even if they live in an un-managed directory. Disable to only show un-managed files in directories which already contain managed files (the default). The purpose is to easily spot new un-managed files in already managed directories. (in both cases, only the un-managed files are shown)"
        self.junk_tooltip = 'Filter out files and directories considered as "unwanted" for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories.  You can disable this, for example if you want to add files to your chezmoi repository which are in a directory named "cache".'

    def compose(self) -> ComposeResult:

        with Horizontal(classes="filter-container"):
            yield Switch(
                value=False, id="includeunmanaged", classes="filter-switch"
            )
            yield Label(
                "Include unmanaged directories",
                id="unmanagedlabel",
                classes="filter-label",
            )
            yield Label(
                "(?)", id="unmanagedtooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.unmanaged_tooltip)

        with Horizontal(classes="filter-container"):
            yield Switch(value=True, id="filterjunk", classes="filter-switch")
            yield Label(
                "Filter unwanted paths", id="unwanted", classes="filter-label"
            )
            yield Label(
                "(?)", id="junktooltip", classes="filter-tooltip"
            ).with_tooltip(tooltip=self.junk_tooltip)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        add_dir_tree = self.screen.query_exactly_one(FilteredAddDirTree)
        if event.switch.id == "includeunmanaged":
            add_dir_tree.include_unmanaged_dirs = event.value
            add_dir_tree.reload()
        elif event.switch.id == "filterjunk":
            add_dir_tree.filter_unwanted = event.value
            add_dir_tree.reload()
