from pathlib import Path

from rich.text import Text
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

from chezmoi_mousse import CM_CFG, theme
from chezmoi_mousse.chezmoi import chezmoi, op_log
from chezmoi_mousse.config import pw_mgr_info
from chezmoi_mousse.containers import (
    ButtonsHorizontal,
    FilterSlider,
    TreeContentSwitcher,
)
from chezmoi_mousse.id_typing import (
    ButtonEnum,
    CharsEnum,
    FilterEnum,
    IdMixin,
    Location,
    OperateIdStr,
    ScreenStr,
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

    check_mark = CharsEnum.check_mark.value

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
        self.log_id = OperateIdStr.operate_log_id
        self.log_qid = f"#{self.log_id}"
        super().__init__(id=ScreenStr.operate_modal)

    def compose(self) -> ComposeResult:
        with Vertical(
            id=OperateIdStr.operate_vertical_id,
            classes=TcssStr.operate_container,
        ):
            yield AutoWarning(tab_str=self.tab_name)
            yield OperateInfo(tab_str=self.tab_name, path=self.path)
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
                        DiffView(tab_name=self.tab_name, view_id=self.diff_id),
                        classes=TcssStr.operate_collapsible,
                        title="file diffs view",
                    )
            yield op_log
            yield ButtonsHorizontal(
                self.tab_name, buttons=self.buttons, location=Location.bottom
            )

    def on_mount(self) -> None:
        log_border_titles = {
            TabStr.apply_tab: str(ButtonEnum.apply_file_btn.value).lower(),
            TabStr.re_add_tab: str(ButtonEnum.re_add_file_btn.value).lower(),
            TabStr.add_tab: str(ButtonEnum.add_file_btn.value).lower(),
        }
        self.query_exactly_one(AutoWarning).add_class(
            TcssStr.operate_auto_warning
        )
        self.query_exactly_one(OperateInfo).add_class(TcssStr.operate_top_path)
        self.query_exactly_one(DiffView).add_class(TcssStr.operate_diff)

        # Add initial log entry
        self.query_one(self.log_qid, RichLog).border_title = (
            f"{log_border_titles[self.tab_name]} log"
        )
        # Set path for either diff or contents view
        if self.tab_name == TabStr.add_tab:
            self.query_one(self.contents_qid, ContentsView).path = self.path
            op_log.log_success("--- ready to run chezmoi add ---")
        elif self.tab_name in (TabStr.apply_tab, TabStr.re_add_tab):
            self.query_one(self.diff_qid, DiffView).path = self.path
            if self.tab_name == TabStr.apply_tab:
                op_log.log_success("--- ready to run chezmoi apply ---")
            elif self.tab_name == TabStr.re_add_tab:
                op_log.log_success("--- ready to run chezmoi re-add ---")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()

        if event.button.id == self.button_id(ButtonEnum.apply_file_btn):
            chezmoi.perform.apply(self.path)
            self.query_one(
                self.button_qid(ButtonEnum.apply_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_apply_btn), Button
            ).label = "Close"
            self.command_has_been_run = True

        elif event.button.id == self.button_id(ButtonEnum.re_add_file_btn):
            chezmoi.perform.re_add(self.path)
            self.query_one(
                self.button_qid(ButtonEnum.re_add_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_re_add_btn), Button
            ).label = "Close"
            self.command_has_been_run = True

        elif event.button.id == self.button_id(ButtonEnum.add_file_btn):
            chezmoi.perform.add(self.path)
            self.query_one(
                self.button_qid(ButtonEnum.add_file_btn), Button
            ).disabled = True
            self.query_one(
                self.button_qid(ButtonEnum.cancel_add_btn), Button
            ).label = "Close"
            self.command_has_been_run = True

        elif event.button.id in (
            self.button_id(ButtonEnum.cancel_apply_btn),
            self.button_id(ButtonEnum.cancel_re_add_btn),
            self.button_id(ButtonEnum.cancel_add_btn),
        ):
            if self.command_has_been_run:
                self.notify("operation completed")
            else:
                self.notify("operation cancelled without changes")
            self.dismiss()


class _BaseTab(Horizontal, IdMixin):

    def update_right_side_content_switcher(self, path: Path):
        self.query_one(
            self.content_switcher_qid(Location.right), Container
        ).border_title = f"{path.relative_to(CM_CFG.destDir)}"
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


class ApplyTab(_BaseTab):

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
            yield TreeContentSwitcher(self.tab_str)

        with Vertical(id=self.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(
                    ButtonEnum.diff_btn,
                    ButtonEnum.contents_btn,
                    ButtonEnum.git_log_btn,
                ),
                location=Location.right,
            )
            with ContentSwitcher(
                id=self.content_switcher_id(Location.right),
                initial=self.view_id(ViewStr.diff_view),
            ):
                yield DiffView(
                    tab_name=self.tab_name,
                    view_id=self.view_id(ViewStr.diff_view),
                )
                yield ContentsView(view_id=self.view_id(ViewStr.contents_view))
                yield GitLogView(view_id=self.view_id(ViewStr.git_log_view))

        yield FilterSlider(
            self.tab_str, filters=(FilterEnum.unchanged, FilterEnum.expand_all)
        )

    def on_mount(self) -> None:
        right_side = self.query_one(
            self.tab_vertical_qid(Location.right), Vertical
        )
        right_side.add_class(TcssStr.tab_right_vertical)
        right_side_content_switcher = self.query_one(
            self.content_switcher_qid(Location.right), ContentSwitcher
        )
        right_side_content_switcher.add_class(TcssStr.content_switcher_right)
        right_side_content_switcher.add_class(TcssStr.top_border_title)

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


class ReAddTab(_BaseTab):

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
            yield TreeContentSwitcher(self.tab_str)

        with Vertical(id=self.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                self.tab_str,
                buttons=(
                    ButtonEnum.diff_btn,
                    ButtonEnum.contents_btn,
                    ButtonEnum.git_log_btn,
                ),
                location=Location.right,
            )

            with ContentSwitcher(
                id=self.content_switcher_id(Location.right),
                initial=self.view_id(ViewStr.diff_view),
            ):
                yield DiffView(
                    tab_name=self.tab_name,
                    view_id=self.view_id(ViewStr.diff_view),
                )
                yield ContentsView(view_id=self.view_id(ViewStr.contents_view))
                yield GitLogView(view_id=self.view_id(ViewStr.git_log_view))

        yield FilterSlider(
            self.tab_str, filters=(FilterEnum.unchanged, FilterEnum.expand_all)
        )

    def on_mount(self) -> None:
        self.query_one(
            self.tab_vertical_qid(Location.right), Vertical
        ).add_class(TcssStr.tab_right_vertical)
        content_switcher_right = self.query_one(
            self.content_switcher_qid(Location.right), ContentSwitcher
        )
        content_switcher_right.add_class(TcssStr.content_switcher_right)
        content_switcher_right.add_class(TcssStr.top_border_title)

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
        with VerticalGroup(id=self.tab_vertical_id(Location.left)):
            yield FilteredDirTree(
                CM_CFG.destDir,
                id=self.tree_id(TreeStr.add_tree),
                classes=TcssStr.dir_tree_widget,
            )

        with Vertical(id=self.tab_vertical_id(Location.right)):
            yield ContentsView(view_id=self.view_id(ViewStr.contents_view))

        yield FilterSlider(
            self.tab_str,
            filters=(FilterEnum.unmanaged_dirs, FilterEnum.unwanted),
        )

    def on_mount(self) -> None:
        right_side = self.query_one(
            self.tab_vertical_qid(Location.right), Vertical
        )
        right_side.border_title = str(CM_CFG.destDir)
        right_side.add_class(TcssStr.tab_right_vertical)
        right_side.add_class(TcssStr.top_border_title)
        left_side = self.query_one(
            self.tab_vertical_qid(Location.left), VerticalGroup
        )
        left_side.border_title = str(CM_CFG.destDir)
        left_side.add_class(TcssStr.tab_left_vertical)
        left_side.add_class(TcssStr.top_border_title)

        tree = self.query_one(self.tree_qid(TreeStr.add_tree), FilteredDirTree)
        tree.show_root = False
        tree.guide_depth = 3

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
        ).border_title = f"{event.node.data.path.relative_to(CM_CFG.destDir)}"

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
        ).border_title = f"{event.node.data.path.relative_to(CM_CFG.destDir)}"

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


class DoctorTab(VerticalScroll, IdMixin):

    def __init__(self, tab_str: TabStr) -> None:
        IdMixin.__init__(self, tab_str)
        super().__init__(id=self.tab_main_horizontal_id)

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

    # do not put this in the on_mount method as textual manages this
    def populate_doctor_data(self) -> None:
        styles = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
            "info": theme.vars["foreground-darken-1"],
        }
        list_view = self.query_exactly_one(ListView)
        table: DataTable[Text] = self.query_exactly_one(DataTable[Text])

        # Add columns if they don't exist
        if not table.columns:
            table.add_columns(*chezmoi.doctor.list_out[0].split())

        for line in chezmoi.doctor.list_out[1:]:
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

        collapsibles = self.query(Collapsible)
        for collapsible in collapsibles:
            title = collapsible.title
            if "template data" in title:
                # Update the Pretty widget with latest template data
                pretty_widget = collapsible.query_one(Pretty)
                pretty_widget.update(chezmoi.template_data.dict_out)
            elif "cat-config" in title:
                # Update the Pretty widget with latest cat-config data
                pretty_widget = collapsible.query_one(Pretty)
                pretty_widget.update(chezmoi.cat_config.list_out)
            elif "ignored" in title:
                # Update the Pretty widget with latest ignored data
                pretty_widget = collapsible.query_one(Pretty)
                pretty_widget.update(chezmoi.ignored.list_out)
