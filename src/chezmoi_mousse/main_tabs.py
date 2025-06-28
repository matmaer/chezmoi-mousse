"""Contains the widgets used to compose the tabs on the main screen of chezmoi-
mousse, except for the Log tab.

Additionally, it contains widgets which are these tabs depend on, if they are
containers.
"""

from datetime import datetime
from pathlib import Path

from rich.text import Text

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
    VerticalGroup,
    VerticalScroll,
)
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Collapsible,
    ContentSwitcher,
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
    ButtonsHorizontal,
    ContentSwitcherLeft,
    ContentSwitcherRight,
    FilterSlider,
)
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    CharsEnum,
    CornerStr,
    LogTabEntry,
    FilterEnum,
    IdMixin,
    SideStr,
    TabStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.widgets import (
    AutoWarning,
    DiffView,
    ExpandedTree,
    FilteredDirTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    NodeData,
    ContentsView,
    RichLog,
    TreeBase,
)


class Operate(ModalScreen[None], IdMixin):
    BINDINGS = [
        Binding(
            key="escape", action="dismiss", description="close", show=False
        )
    ]

    def __init__(
        self, tab_name: TabStr, *, path: Path, buttons: tuple[ButtonEnum, ...]
    ) -> None:
        IdMixin.__init__(self, tab_name)
        self.tab_name = tab_name
        self.path = path
        self.buttons = buttons
        self.diff_id = self.view_id(ViewStr.diff_view, operate=True)
        self.diff_qid = self.view_qid(ViewStr.diff_view, operate=True)
        self.contents_id = self.view_id(ViewStr.contents_view, operate=True)
        self.contents_qid = self.view_qid(ViewStr.contents_view, operate=True)
        self.info_id = f"{tab_name}_operation_info"
        self.info_qid = f"#{self.info_id}"
        self.log_id = f"{tab_name}_operate_log"
        self.log_qid = f"#{self.log_id}"
        super().__init__(id="operate_screen", classes="operate-screen")

    def compose(self) -> ComposeResult:
        with Vertical(id="operate_container", classes="operate-container"):
            if (
                self.tab_name == TabStr.add_tab
                or self.tab_name == TabStr.re_add_tab
            ):
                yield AutoWarning(classes="operate-auto-warning")
            yield Static(
                f"{self.path}", id=self.info_id, classes="operate-top-path"
            )
            if self.tab_name == TabStr.add_tab:
                with Container(
                    id="collapsible_container", classes="collapsible-container"
                ):
                    yield Collapsible(
                        ContentsView(view_id=self.contents_id),
                        classes="operate-collapsible",
                        title="file contents view",
                    )
            else:
                with Container(
                    id="collapsible_container", classes="collapsible-container"
                ):
                    yield Collapsible(
                        DiffView(tab_name=self.tab_name, view_id=self.diff_id),
                        classes="operate-collapsible",
                        title="file diffs view",
                    )
            yield RichLog(id=self.log_id, classes="operate-log")
            yield ButtonsHorizontal(
                self.tab_name,
                buttons=self.buttons,
                corner_str=CornerStr.bottom_right,
            )

    def on_mount(self) -> None:
        # Set border titles
        border_titles = {
            TabStr.apply_tab: CharsEnum.apply.value,
            TabStr.re_add_tab: CharsEnum.re_add.value,
            TabStr.add_tab: CharsEnum.add.value,
        }
        operation_info = self.query_one(self.info_qid, Static)
        operation_info.border_title = border_titles[self.tab_name]
        self.query_one(self.log_qid, RichLog).border_title = (
            f"{self.tab_name} log"
        )

        # Query the relevant view based on the tab type
        if self.tab_name == TabStr.add_tab:
            view = self.query_one(self.contents_qid, ContentsView)
        else:
            view = self.query_one(self.diff_qid, DiffView)

        # Set path and classes
        view.path = self.path
        view.add_class("operate-view")
        self.query_exactly_one(ButtonsHorizontal).add_class(
            "operate-buttons-horizontal"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        op_log = self.query_one(self.log_qid, RichLog)
        if event.button.id == self.button_id(ButtonEnum.apply_file_btn):
            self.notify(f"Not yet implemented for {op_log}.")
        elif event.button.id == self.button_id(ButtonEnum.re_add_file_btn):
            self.notify(f"Not yet implemented for {op_log}.")
        elif event.button.id == self.button_id(ButtonEnum.add_file_btn):
            self.notify(f"Not yet implemented for {op_log}.")
        elif event.button.id == self.button_id(ButtonEnum.cancel_apply_btn):
            self.dismiss()
        elif event.button.id == self.button_id(ButtonEnum.cancel_re_add_btn):
            self.dismiss()
        elif event.button.id == self.button_id(ButtonEnum.cancel_add_btn):
            self.dismiss()


class BaseTab(Horizontal, IdMixin):
    """Base class for ApplyTab and ReAddTab."""

    def update_right_side_content_switcher(self, path: Path):
        self.query_one(
            self.content_switcher_qid(SideStr.right), Container
        ).border_title = f"{path.relative_to(chezmoi.dest_dir)}"
        self.query_one(
            self.view_qid(ViewStr.contents_view), ContentsView
        ).path = path
        self.query_one(self.view_qid(ViewStr.diff_view), DiffView).path = path
        self.query_one(
            self.view_qid(ViewStr.git_log_view), GitLogView
        ).path = path

    def on_tree_node_selected(
        self, event: TreeBase.NodeSelected[NodeData]
    ) -> None:
        assert event.node.data is not None
        self.update_right_side_content_switcher(event.node.data.path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Tree/List Switch
        if event.button.id == self.button_id(ButtonEnum.tree_btn):
            expand_all_switch = self.query_one(
                self.switch_qid(FilterEnum.expand_all), Switch
            )
            expand_all_switch.disabled = False
            if expand_all_switch.value:
                self.query_one(
                    self.content_switcher_qid(SideStr.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.content_switcher_qid(SideStr.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.managed_tree)
        elif event.button.id == self.button_id(ButtonEnum.list_btn):
            self.query_one(
                self.content_switcher_qid(SideStr.left), ContentSwitcher
            ).current = self.tree_id(TreeStr.flat_tree)
            self.query_one(
                self.switch_qid(FilterEnum.expand_all), Switch
            ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.button_id(ButtonEnum.contents_btn):
            self.query_one(
                self.content_switcher_qid(SideStr.right), ContentSwitcher
            ).current = self.view_id(ViewStr.contents_view)
        elif event.button.id == self.button_id(ButtonEnum.diff_btn):
            self.query_one(
                self.content_switcher_qid(SideStr.right), ContentSwitcher
            ).current = self.view_id(ViewStr.diff_view)
        elif event.button.id == self.button_id(ButtonEnum.git_log_btn):
            self.query_one(
                self.content_switcher_qid(SideStr.right), ContentSwitcher
            ).current = self.view_id(ViewStr.git_log_view)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.switch_id(FilterEnum.unchanged):
            tree_pairs: list[
                tuple[TreeStr, type[ExpandedTree | ManagedTree | FlatTree]]
            ] = [
                (TreeStr.expanded_tree, ExpandedTree),
                (TreeStr.managed_tree, ManagedTree),
                (TreeStr.flat_tree, FlatTree),
            ]
            for tree_str, tree_cls in tree_pairs:
                self.query_one(self.tree_qid(tree_str), tree_cls).unchanged = (
                    event.value
                )
        elif event.switch.id == self.switch_id(FilterEnum.expand_all):
            if event.value:
                self.query_one(
                    self.content_switcher_qid(SideStr.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.content_switcher_qid(SideStr.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.managed_tree)


class ApplyTab(BaseTab):

    BINDINGS = [
        Binding(key="C", action="apply_diff", description="chezmoi-apply")
    ]

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        self.tab_str: TabStr = tab_str
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(SideStr.left), classes="tab-left-vertical"
        ):
            # yield ButtonsTopLeft(self.tab_str)
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(ButtonEnum.tree_btn, ButtonEnum.list_btn),
                corner_str=CornerStr.top_left,
            )
            yield ContentSwitcherLeft(self.tab_str)

        with Vertical(
            id=self.tab_vertical_id(SideStr.right),
            classes="tab-right-vertical",
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(
                    ButtonEnum.diff_btn,
                    ButtonEnum.contents_btn,
                    ButtonEnum.git_log_btn,
                ),
                corner_str=CornerStr.top_right,
            )
            yield ContentSwitcherRight(self.tab_str)

        yield FilterSlider(
            self.tab_str, filters=(FilterEnum.unchanged, FilterEnum.expand_all)
        )

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:

        diff_button = self.query_one(self.button_qid(ButtonEnum.diff_btn))

        content_switcher = self.query_one(
            self.content_switcher_qid(SideStr.right), ContentSwitcher
        )
        # current returns the id of the currently active view
        active_view_id: str | None = content_switcher.current
        if active_view_id == self.view_id(
            ViewStr.diff_view
        ) or diff_button.has_class("last-clicked"):
            return True
        else:
            return None

    def action_toggle_filter_slider(self) -> None:
        self.query_one(self.filter_slider_qid, VerticalGroup).toggle_class(
            "-visible"
        )

    def action_apply_diff(self) -> None:
        diff_view = self.query_one(self.view_qid(ViewStr.diff_view), DiffView)
        current_path = getattr(diff_view, "path")
        self.app.push_screen(
            Operate(
                self.tab_str,
                buttons=(
                    ButtonEnum.apply_file_btn,
                    ButtonEnum.cancel_apply_btn,
                ),
                path=current_path,
            )
        )


class ReAddTab(BaseTab):

    BINDINGS = [
        Binding(key="C", action="re_add_diff", description="chezmoi-re-add")
    ]

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        self.tab_str: TabStr = tab_str
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(SideStr.left), classes="tab-left-vertical"
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(ButtonEnum.tree_btn, ButtonEnum.list_btn),
                corner_str=CornerStr.top_left,
            )
            yield ContentSwitcherLeft(self.tab_str)

        with Vertical(
            id=self.tab_vertical_id(SideStr.right),
            classes="tab-right-vertical",
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(
                    ButtonEnum.diff_btn,
                    ButtonEnum.contents_btn,
                    ButtonEnum.git_log_btn,
                ),
                corner_str=CornerStr.top_right,
            )
            yield ContentSwitcherRight(self.tab_str)

        yield FilterSlider(
            self.tab_str, filters=(FilterEnum.unchanged, FilterEnum.expand_all)
        )

    def action_toggle_filter_slider(self) -> None:
        self.query_one(self.filter_slider_qid, VerticalGroup).toggle_class(
            "-visible"
        )

    def action_re_add_diff(self) -> None:
        diff_view = self.query_one(self.view_qid(ViewStr.diff_view), DiffView)
        current_path = getattr(diff_view, "path")
        self.app.push_screen(
            Operate(
                self.tab_str,
                buttons=(
                    ButtonEnum.re_add_file_btn,
                    ButtonEnum.cancel_re_add_btn,
                ),
                path=current_path,
            )
        )


class AddTab(Horizontal, IdMixin):

    BINDINGS = [
        Binding(key="C", action="add_contents", description="chezmoi-add")
    ]

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        self.tab_str: TabStr = tab_str
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(SideStr.left),
            classes="tab-left-vertical top-border-title",
        ):
            yield FilteredDirTree(
                chezmoi.dest_dir,
                id=self.tree_id(TreeStr.add_tree),
                classes="dir-tree-widget",
            )

        with Vertical(
            id=self.tab_vertical_id(SideStr.right),
            classes="tab-right-vertical top-border-title",
        ):
            yield ContentsView(view_id=self.view_id(ViewStr.contents_view))

        yield FilterSlider(
            self.tab_str,
            filters=(FilterEnum.unmanaged_dirs, FilterEnum.unwanted),
        )

    def on_mount(self) -> None:
        self.query_one(
            self.tab_vertical_qid(SideStr.right), Vertical
        ).border_title = chezmoi.dest_dir_str
        self.query_one(
            self.tab_vertical_qid(SideStr.left), VerticalGroup
        ).border_title = chezmoi.dest_dir_str

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        self.query_one(
            self.view_qid(ViewStr.contents_view), ContentsView
        ).path = event.node.data.path
        self.query_one(
            self.tab_vertical_qid(SideStr.right), Vertical
        ).border_title = (
            f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
        )

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one(
            self.view_qid(ViewStr.contents_view), ContentsView
        ).path = event.node.data.path
        self.query_one(
            self.tab_vertical_qid(SideStr.right), Vertical
        ).border_title = (
            f"{event.node.data.path.relative_to(chezmoi.dest_dir)}"
        )

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(self.tree_qid(TreeStr.add_tree), FilteredDirTree)
        if event.switch.id == self.switch_id(FilterEnum.unmanaged_dirs):
            tree.unmanaged_dirs = event.value
            tree.reload()
        elif event.switch.id == self.switch_id(FilterEnum.unwanted):
            tree.unwanted = event.value
            tree.reload()

    def action_toggle_filter_slider(self) -> None:
        self.query_one(self.filter_slider_qid, VerticalGroup).toggle_class(
            "-visible"
        )

    def action_add_contents(self) -> None:
        contents_view = self.query_one(
            self.view_qid(ViewStr.contents_view), ContentsView
        )
        current_path = getattr(contents_view, "path")
        self.app.push_screen(
            Operate(
                self.tab_str,
                buttons=(ButtonEnum.add_file_btn, ButtonEnum.cancel_add_btn),
                path=current_path,
            )
        )


class DoctorTab(VerticalScroll):

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
        table: DataTable[Text] = self.query_exactly_one(DataTable[Text])
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


class LogTab(RichLog):

    splash_log: list[LogTabEntry] | None = None

    def add(self, chezmoi_io: LogTabEntry) -> None:
        time_stamp = datetime.now().strftime("%H:%M:%S")
        # Turn the full command list into string, remove elements not useful
        # to display in the log
        trimmed_cmd: list[str] = [
            _
            for _ in chezmoi_io.long_command
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
        self.write(chezmoi_io.message)

    def log_callback(self, chezmoi_io: LogTabEntry) -> None:
        self.add(chezmoi_io)

    def on_mount(self) -> None:
        chezmoi_mousse.chezmoi.log_tab_callback = self.log_callback
        self.write_splash_log()

    @work(thread=True)
    def write_splash_log(self) -> None:
        if self.splash_log is not None:
            for cmd in self.splash_log:
                self.add(cmd)
