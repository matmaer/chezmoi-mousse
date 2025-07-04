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
    FilterEnum,
    IdMixin,
    Location,
    OperateIdStr,
    TabStr,
    TcssStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.widgets import (
    AutoWarning,
    ContentsView,
    DiffView,
    ExpandedTree,
    FilteredDirTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    NodeData,
    OperateInfo,
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
        self.command_has_been_run = False
        self.diff_id = self.view_id(ViewStr.diff_view, operate=True)
        self.diff_qid = self.view_qid(ViewStr.diff_view, operate=True)
        self.contents_id = self.view_id(ViewStr.contents_view, operate=True)
        self.contents_qid = self.view_qid(ViewStr.contents_view, operate=True)
        self.path_info_id = OperateIdStr.operate_top_path_id
        self.path_info_qid = f"#{self.path_info_id}"
        self.log_id = OperateIdStr.operate_log_id
        self.log_qid = f"#{self.log_id}"
        super().__init__(id=OperateIdStr.operate_screen_id)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=OperateIdStr.operate_vertical_id,
            classes=TcssStr.operate_container,
        ):
            if self.tab_name in (TabStr.add_tab, TabStr.re_add_tab):
                yield AutoWarning(classes=TcssStr.operate_auto_warning)
            yield Static(
                f"{self.path}",
                id=self.path_info_id,
                classes=TcssStr.operate_top_path,
            )
            yield OperateInfo(tab_name=self.tab_name)
            if self.tab_name == TabStr.add_tab:
                with Container(
                    id=OperateIdStr.operate_collapsible_id,
                    classes=TcssStr.collapsible_container,
                ):
                    yield Collapsible(
                        ContentsView(view_id=self.contents_id),
                        classes=TcssStr.operate_collapsible,
                        title="file contents view",
                    )
            else:
                with Container(
                    id=OperateIdStr.operate_collapsible_id,
                    classes=TcssStr.collapsible_container,
                ):
                    yield Collapsible(
                        DiffView(
                            tab_name=self.tab_name,
                            view_id=self.diff_id,
                            classes=TcssStr.operate_diff,
                        ),
                        classes=TcssStr.operate_collapsible,
                        title="file diffs view",
                    )
            yield RichLog(
                id=self.log_id,
                highlight=True,
                wrap=True,
                classes=TcssStr.operate_log,
            )
            yield ButtonsHorizontal(
                self.tab_name, buttons=self.buttons, location=Location.bottom
            )

    def on_mount(self) -> None:
        # Set border titles
        info_border_titles = {
            TabStr.apply_tab: CharsEnum.apply.value,
            TabStr.re_add_tab: CharsEnum.re_add.value,
            TabStr.add_tab: CharsEnum.add.value,
        }
        log_border_titles = {
            TabStr.apply_tab: str(ButtonEnum.apply_file_btn.value).lower(),
            TabStr.re_add_tab: str(ButtonEnum.re_add_file_btn.value).lower(),
            TabStr.add_tab: str(ButtonEnum.add_file_btn.value).lower(),
        }
        self.query_one(self.path_info_qid, Static).border_subtitle = (
            info_border_titles[self.tab_name]
        )

        # Add initial log entry
        operate_log = self.query_one(self.log_qid, RichLog)
        operate_log.border_title = f"{log_border_titles[self.tab_name]} log"
        operate_log.write(
            f"[{datetime.now().strftime('%H:%M:%S')}] ready to run command"
        )

        # Set path for either diff or contents view
        if self.tab_name == TabStr.add_tab:
            self.query_one(self.contents_qid, ContentsView).path = self.path
        else:
            self.query_one(self.diff_qid, DiffView).path = self.path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        op_log = self.query_one(self.log_qid, RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if event.button.id == self.button_id(ButtonEnum.apply_file_btn):
            op_log.write(f"[{timestamp}] {chezmoi.perform.apply(self.path)}")
            self.query_one(
                self.button_qid(ButtonEnum.apply_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_apply_btn), Button
            ).label = "Close"
            self.command_has_been_run = True
            self.hide_warnings()

        elif event.button.id == self.button_id(ButtonEnum.re_add_file_btn):
            op_log.write(f"[{timestamp}] {chezmoi.perform.re_add(self.path)}")
            self.query_one(
                self.button_qid(ButtonEnum.re_add_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_re_add_btn), Button
            ).label = "Close"
            self.command_has_been_run = True
            self.hide_warnings()

        elif event.button.id == self.button_id(ButtonEnum.add_file_btn):
            op_log.write(f"[{timestamp}] {chezmoi.perform.add(self.path)}")
            self.query_one(
                self.button_qid(ButtonEnum.add_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_add_btn), Button
            ).label = "Close"
            self.command_has_been_run = True
            self.hide_warnings()

        elif event.button.id in (
            self.button_id(ButtonEnum.cancel_apply_btn),
            self.button_id(ButtonEnum.cancel_re_add_btn),
            self.button_id(ButtonEnum.cancel_add_btn),
        ):
            if self.command_has_been_run:
                self.notify("operation completed, output available in Log tab")
            else:
                self.notify("operation cancelled without changes")
            self.dismiss()

    def hide_warnings(self) -> None:
        if self.tab_name in (TabStr.add_tab, TabStr.re_add_tab):
            self.query_exactly_one(AutoWarning).remove()
        self.query_exactly_one(Collapsible).remove()
        self.query_exactly_one(OperateInfo).remove()


class BaseTab(Horizontal, IdMixin):
    """Base class for ApplyTab and ReAddTab."""

    def update_right_side_content_switcher(self, path: Path):
        self.query_one(
            self.content_switcher_qid(Location.right), Container
        ).border_title = f"{path.relative_to(chezmoi.dest_dir)}"
        self.query_one(
            self.view_qid(ViewStr.contents_view), ContentsView
        ).path = path
        self.query_one(self.view_qid(ViewStr.diff_view), DiffView).path = path
        self.query_one(
            self.view_qid(ViewStr.git_log_view), GitLogView
        ).path = path
        # Refresh bindings when path changes for the operate bindings
        self.refresh_bindings()

    def check_action(
        self, action: str, parameters: tuple[object, ...]
    ) -> bool | None:
        if action in ("apply_diff", "re_add_diff"):
            try:
                diff_button = self.query_one(
                    self.button_qid(ButtonEnum.diff_btn)
                )
            except Exception:
                # If diff button not found, default to invisible
                return False

            if diff_button.has_class(TcssStr.last_clicked):
                active_path = self.query_one(
                    self.view_qid(ViewStr.diff_view), DiffView
                ).path
                # Check if the current path has a diff available
                tab_str = getattr(self, "tab_str")
                if (
                    active_path in chezmoi.managed_status[tab_str].files
                    and chezmoi.managed_status[tab_str].files[active_path]
                    != "X"
                ):
                    return True  # Visible and clickable
                else:
                    return None  # Visible but disabled when diff view is active but no valid diff
            return False  # Invisible when diff view is not active
        return False

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
                    self.content_switcher_qid(Location.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.content_switcher_qid(Location.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.managed_tree)
        elif event.button.id == self.button_id(ButtonEnum.list_btn):
            self.query_one(
                self.content_switcher_qid(Location.left), ContentSwitcher
            ).current = self.tree_id(TreeStr.flat_tree)
            self.query_one(
                self.switch_qid(FilterEnum.expand_all), Switch
            ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.button_id(ButtonEnum.contents_btn):
            self.query_one(
                self.content_switcher_qid(Location.right), ContentSwitcher
            ).current = self.view_id(ViewStr.contents_view)
            # Refresh bindings when switching views
            self.refresh_bindings()
        elif event.button.id == self.button_id(ButtonEnum.diff_btn):
            self.query_one(
                self.content_switcher_qid(Location.right), ContentSwitcher
            ).current = self.view_id(ViewStr.diff_view)
            # Refresh bindings when switching views
            self.refresh_bindings()
        elif event.button.id == self.button_id(ButtonEnum.git_log_btn):
            self.query_one(
                self.content_switcher_qid(Location.right), ContentSwitcher
            ).current = self.view_id(ViewStr.git_log_view)
            # Refresh bindings when switching views
            self.refresh_bindings()

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
                    self.content_switcher_qid(Location.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.content_switcher_qid(Location.left), ContentSwitcher
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
            id=self.tab_vertical_id(Location.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(ButtonEnum.tree_btn, ButtonEnum.list_btn),
                location=Location.left,
            )
            yield ContentSwitcherLeft(self.tab_str)

        with Vertical(
            id=self.tab_vertical_id(Location.right),
            classes=TcssStr.tab_right_vertical,
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(
                    ButtonEnum.diff_btn,
                    ButtonEnum.contents_btn,
                    ButtonEnum.git_log_btn,
                ),
                location=Location.right,
            )
            yield ContentSwitcherRight(self.tab_str)

        yield FilterSlider(
            self.tab_str, filters=(FilterEnum.unchanged, FilterEnum.expand_all)
        )

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
            id=self.tab_vertical_id(Location.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(ButtonEnum.tree_btn, ButtonEnum.list_btn),
                location=Location.left,
            )
            yield ContentSwitcherLeft(self.tab_str)

        with Vertical(
            id=self.tab_vertical_id(Location.right),
            classes=TcssStr.tab_right_vertical,
        ):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(
                    ButtonEnum.diff_btn,
                    ButtonEnum.contents_btn,
                    ButtonEnum.git_log_btn,
                ),
                location=Location.right,
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
            id=self.tab_vertical_id(Location.left),
            classes=f"{TcssStr.tab_left_vertical} {TcssStr.top_border_title}",
        ):
            yield FilteredDirTree(
                chezmoi.dest_dir,
                id=self.tree_id(TreeStr.add_tree),
                classes=TcssStr.dir_tree_widget,
            )

        with Vertical(
            id=self.tab_vertical_id(Location.right),
            classes=f"{TcssStr.tab_right_vertical} {TcssStr.top_border_title}",
        ):
            yield ContentsView(view_id=self.view_id(ViewStr.contents_view))

        yield FilterSlider(
            self.tab_str,
            filters=(FilterEnum.unmanaged_dirs, FilterEnum.unwanted),
        )

    def on_mount(self) -> None:
        self.query_one(
            self.tab_vertical_qid(Location.right), Vertical
        ).border_title = chezmoi.dest_dir_str
        self.query_one(
            self.tab_vertical_qid(Location.left), VerticalGroup
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
            self.tab_vertical_qid(Location.right), Vertical
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
            self.tab_vertical_qid(Location.right), Vertical
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

    splash_log: list[str] | None = None

    # def add(self, log_text: str) -> None:
    #     self.write(log_text)

    def log_callback(self, log_text: str) -> None:
        self.write(log_text)

    def on_mount(self) -> None:
        chezmoi_mousse.chezmoi.log_tab_callback = self.log_callback
        self.write_splash_log()

    @work(thread=True)
    def write_splash_log(self) -> None:
        if self.splash_log is not None:
            for cmd in self.splash_log:
                self.write(cmd)
