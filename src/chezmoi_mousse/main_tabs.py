"""Contains the widgets used to compose the tabs on the main screen of chezmoi-
mousse, except for the Log tab.

Additionally, it contains widgets which are these tabs depend on, if they are
containers.
"""

from datetime import datetime

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Horizontal,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import (
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

import chezmoi_mousse.chezmoi
import chezmoi_mousse.theme as theme
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import pw_mgr_info
from chezmoi_mousse.containers import (
    ContentSwitcherLeft,
    ContentSwitcherRight,
    EventMixin,
    FilterSwitch,
    IdMixin,
    ButtonEnumsLeft,
    ButtonEnumsRight,
)
from chezmoi_mousse.id_typing import ComponentStr, FilterEnum, TabEnum, SideStr
from chezmoi_mousse.widgets import FilteredDirTree, GitLog, PathView, RichLog


class ApplyTab(Horizontal, IdMixin, EventMixin):

    BINDINGS = [
        Binding(key="W,w", action="apply_path", description="chezmoi-apply"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    def __init__(self, tab_key: TabEnum) -> None:
        IdMixin.__init__(self, TabEnum.apply_tab)
        self.tab_key: TabEnum = tab_key
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(SideStr.left), classes="tab-left-vertical"
        ):
            yield ButtonEnumsLeft(self.tab_key)
            yield ContentSwitcherLeft(self.tab_key)

        with Vertical(
            id=self.tab_vertical_id(SideStr.right),
            classes="tab-right-vertical",
        ):
            yield ButtonEnumsRight(self.tab_key)
            yield ContentSwitcherRight(self.tab_key)

        with VerticalGroup(
            id=self.filter_slider_id, classes="filters-vertical"
        ):
            yield FilterSwitch(
                self.tab_key,
                FilterEnum.unchanged,
                classes="filter-horizontal padding-bottom-once",
            )
            yield FilterSwitch(
                self.tab_key,
                FilterEnum.expand_all,
                classes="filter-horizontal",
            )

    def action_apply_path(self) -> None:
        self.notify("to implement")

    def action_toggle_filter_slider(self) -> None:
        """Toggle the visibility of the filter slider."""
        self.query_one(
            f"#{self.filter_slider_id}", VerticalGroup
        ).toggle_class("-visible")


class ReAddTab(Horizontal, IdMixin, EventMixin):

    BINDINGS = [
        Binding(key="A,a", action="re_add_path", description="chezmoi-re-add"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    def __init__(self, tab_key: TabEnum) -> None:
        IdMixin.__init__(self, TabEnum.re_add_tab)
        self.tab_key: TabEnum = tab_key
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(SideStr.left), classes="tab-left-vertical"
        ):
            yield ButtonEnumsLeft(self.tab_key)
            yield ContentSwitcherLeft(self.tab_key)

        with Vertical(
            id=self.tab_vertical_id(SideStr.right),
            classes="tab-right-vertical",
        ):
            yield ButtonEnumsRight(self.tab_key)
            yield ContentSwitcherRight(self.tab_key)

        with VerticalGroup(
            id=self.filter_slider_id, classes="filters-vertical"
        ):
            yield FilterSwitch(
                self.tab_key,
                FilterEnum.unchanged,
                classes="filter-horizontal padding-bottom-once",
            )
            yield FilterSwitch(
                self.tab_key,
                FilterEnum.expand_all,
                classes="filter-horizontal",
            )

    def action_re_add_path(self) -> None:
        self.notify("to implement")

    def action_toggle_filter_slider(self) -> None:
        """Toggle the visibility of the filter slider."""
        self.query_one(
            f"#{self.filter_slider_id}", VerticalGroup
        ).toggle_class("-visible")


class AddTab(Horizontal, IdMixin):

    BINDINGS = [
        Binding(key="A,a", action="add_path", description="chezmoi-add"),
        Binding(
            key="F,f",
            action="toggle_filter_slider",
            description="toggle-filters",
        ),
    ]

    def __init__(self, tab_key: TabEnum) -> None:
        IdMixin.__init__(self, tab_key)
        self.tab_key: TabEnum = tab_key
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(SideStr.left),
            classes="tab-left-vertical top-border-title",
        ):
            yield FilteredDirTree(
                chezmoi.dest_dir,
                id=self.component_id(ComponentStr.add_tree),
                classes="dir-tree-widget",
            )

        with Vertical(
            id=self.tab_vertical_id(SideStr.right),
            classes="tab-right-vertical top-border-title",
        ):
            yield PathView(self.tab_key)

        with VerticalGroup(
            id=self.filter_slider_id, classes="filters-vertical"
        ):
            yield FilterSwitch(
                self.tab_key,
                FilterEnum.unmanaged_dirs,
                classes="filter-horizontal padding-bottom-once",
            )
            yield FilterSwitch(
                self.tab_key, FilterEnum.unwanted, classes="filter-horizontal"
            )

    def on_mount(self) -> None:
        self.query_one(
            f"#{self.tab_vertical_id(SideStr.right)}", Vertical
        ).border_title = chezmoi.dest_dir_str
        self.query_one(
            f"#{self.tab_vertical_id(SideStr.left)}", VerticalGroup
        ).border_title = chezmoi.dest_dir_str

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        self.query_one(
            f"#{self.component_id(ComponentStr.path_view)}", PathView
        ).path = event.node.data.path
        self.query_one(
            f"#{self.tab_vertical_id(SideStr.right)}", Vertical
        ).border_title = (
            f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
        )

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one(
            f"#{self.component_id(ComponentStr.path_view)}", PathView
        ).path = event.node.data.path
        self.query_one(
            f"#{self.tab_vertical_id(SideStr.right)}", Vertical
        ).border_title = (
            f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            f"#{self.component_id(ComponentStr.add_tree)}", FilteredDirTree
        )
        if event.switch.id == self.filter_switch_id(FilterEnum.unmanaged_dirs):
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == self.filter_switch_id(FilterEnum.unwanted):
            tree.unwanted = event.value
            tree.reload()

    def action_add_path(self) -> None:
        self.notify(f"to_implement: {self.tab_name} tab action 'add_path'")

    def action_toggle_filter_slider(self) -> None:
        """Toggle the visibility of the filter slider."""
        self.query_one(
            f"#{self.filter_slider_id}", VerticalGroup
        ).toggle_class("-visible")


class DoctorTab(VerticalScroll):

    BINDINGS = [
        Binding(key="C,c", action="open_config", description="chezmoi-config"),
        Binding(
            key="G,g",
            action="git_log",
            description="show-git-log",
            tooltip="git log from your chezmoi repository",
        ),
    ]

    class ConfigDumpModal(ModalScreen):

        BINDINGS = [
            Binding(
                key="escape", action="dismiss", description="close", show=False
            )
        ]

        def compose(self) -> ComposeResult:
            yield Pretty(chezmoi.dump_config.dict_out)

        def on_mount(self) -> None:
            self.add_class("doctor-modal")
            self.border_title = "chezmoi dump-config - command output"
            self.border_subtitle = "double click or escape to close"

        def on_click(self, event: Click) -> None:
            event.stop()
            if event.chain == 2:
                self.dismiss()

    class GitLogModal(ModalScreen):

        BINDINGS = [
            Binding(
                key="escape", action="dismiss", description="close", show=False
            )
        ]

        def compose(self) -> ComposeResult:
            yield GitLog(TabEnum.doctor_tab)

        def on_mount(self) -> None:
            self.add_class("doctor-modal")
            self.border_title = "chezmoi git log - command output"
            self.border_subtitle = "double click or escape to close"

        def on_click(self, event: Click) -> None:
            event.stop()
            if event.chain == 2:
                self.dismiss()

    def compose(self) -> ComposeResult:

        with Horizontal():
            yield DataTable(show_cursor=False)
        with VerticalGroup():
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
            yield Collapsible(ListView(), title="Commands Not Found")

    def on_mount(self) -> None:

        styles = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
            "info": theme.vars["foreground-darken-1"],
        }
        list_view = self.query_exactly_one(ListView)
        table = self.query_exactly_one(DataTable)
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
                            Label("Not Found in $PATH."),
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
                    Text(cell_text, style=styles["warning"])
                    for cell_text in row
                ]
                table.add_row(*row)
            else:
                row = [Text(cell_text) for cell_text in row]
                table.add_row(*row)

    def action_open_config(self) -> None:
        self.app.push_screen(DoctorTab.ConfigDumpModal())

    def action_git_log(self) -> None:
        self.app.push_screen(DoctorTab.GitLogModal())


class CommandLog(RichLog):

    splash_command_log: list[tuple[list, str]] | None = None

    def add(self, chezmoi_io: tuple[list, str]) -> None:
        time_stamp = datetime.now().strftime("%H:%M:%S")
        # Turn the full command list into string, remove elements not useful
        # to display in the log
        trimmed_cmd = [
            _
            for _ in chezmoi_io[0]
            if _
            not in (
                "--no-pager"
                "--color=off"
                "--no-tty"
                "--format=json"
                "--path-style=absolute"
                "--path-style=source-absolute"
                "--no-color"
                "--no-decorate"
                "--date-order"
                "--no-expand-tabs"
                "--format=%ar by %cn;%s"
            )
        ]
        pretty_cmd = " ".join(trimmed_cmd)
        self.write(f"{time_stamp} {pretty_cmd}")
        if chezmoi_io[1]:
            self.write(chezmoi_io[1])
        else:
            self.write("Output: to be implemented")

    def on_mount(self) -> None:
        def log_callback(chezmoi_io: tuple[list, str]) -> None:
            self.add(chezmoi_io)

        chezmoi_mousse.chezmoi.command_log_callback = log_callback

        if self.splash_command_log is not None:
            for cmd in self.splash_command_log:
                self.add(cmd)
