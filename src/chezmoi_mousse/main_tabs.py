from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Horizontal,
    ScrollableContainer,
    Vertical,
    VerticalGroup,
)
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
from chezmoi_mousse.chezmoi import chezmoi
from chezmoi_mousse.config import FLOW, pw_mgr_info
from chezmoi_mousse.containers import (
    ButtonsHorizontal,
    FilterSlider,
    InitCloneRepo,
    InitNewRepo,
    InitPurgeRepo,
    TreeContentSwitcher,
)
from chezmoi_mousse.id_typing import (
    Buttons,
    DoctorEnum,
    Filters,
    Id,
    Location,
    TabIds,
    TabStr,
    TcssStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    ExpandedTree,
    FilteredDirTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    NodeData,
    TreeBase,
)


class OperateTabsBase(Horizontal):

    def __init__(self, *, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        super().__init__(id=tab_ids.tab_name)

    def update_right_side_content_switcher(self, path: Path):
        self.query_one(
            self.tab_ids.content_switcher_qid(Location.right), Container
        ).border_title = f"{path.relative_to(CM_CFG.destDir)}"
        # TODO: update on_button_press for each individual button
        self.query_one(
            self.tab_ids.view_qid(ViewStr.contents_view), ContentsView
        ).path = path
        self.query_one(
            self.tab_ids.view_qid(ViewStr.diff_view), DiffView
        ).path = path
        self.query_one(
            self.tab_ids.view_qid(ViewStr.git_log_view), GitLogView
        ).path = path

    def disable_buttons(self, buttons_to_update: tuple[Buttons, ...]) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(
                self.tab_ids.button_qid(button_enum), Button
            )
            button.disabled = True
            if button_enum == Buttons.add_dir_btn:
                button.tooltip = "not yet implemented"
                continue
            button.tooltip = "select a file to enable operations"

    def enable_buttons(self, buttons_to_update: tuple[Buttons, ...]) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(
                self.tab_ids.button_qid(button_enum), Button
            )
            if button_enum == Buttons.add_dir_btn:
                button.tooltip = "not yet implemented"
                continue
            button.disabled = False
            button.tooltip = None

    def on_tree_node_selected(
        self, event: TreeBase.NodeSelected[NodeData]
    ) -> None:
        event.stop()
        assert event.node.data is not None
        self.update_right_side_content_switcher(event.node.data.path)

        buttons_to_update: tuple[Buttons, ...] = ()
        if self.tab_ids.tab_name == TabStr.apply_tab:
            buttons_to_update = (
                Buttons.apply_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        elif self.tab_ids.tab_name == TabStr.re_add_tab:
            buttons_to_update = (
                Buttons.re_add_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        elif self.tab_ids.tab_name == TabStr.add_tab:
            buttons_to_update = (Buttons.add_file_btn, Buttons.add_dir_btn)
        else:
            return
        if event.node.allow_expand:
            self.disable_buttons(buttons_to_update)
        else:
            self.enable_buttons(buttons_to_update)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Tree/List Switch
        event.stop()
        if event.button.id == self.tab_ids.button_id(Buttons.tree_tab):
            expand_all_switch = self.query_one(
                self.tab_ids.switch_qid(Filters.expand_all), Switch
            )
            expand_all_switch.disabled = False
            if expand_all_switch.value:
                self.query_one(
                    self.tab_ids.content_switcher_qid(Location.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.tab_ids.content_switcher_qid(Location.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(TreeStr.managed_tree)
        elif event.button.id == self.tab_ids.button_id(Buttons.list_tab):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.left),
                ContentSwitcher,
            ).current = self.tab_ids.tree_id(TreeStr.flat_tree)
            self.query_one(
                self.tab_ids.switch_qid(Filters.expand_all), Switch
            ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.tab_ids.button_id(Buttons.contents_tab):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(ViewStr.contents_view)

        elif event.button.id == self.tab_ids.button_id(Buttons.diff_tab):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(ViewStr.diff_view)

        elif event.button.id == self.tab_ids.button_id(Buttons.git_log_tab):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(ViewStr.git_log_view)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.tab_ids.switch_id(Filters.unchanged):
            tree_pairs: list[
                tuple[TreeStr, type[ExpandedTree | ManagedTree | FlatTree]]
            ] = [
                (TreeStr.expanded_tree, ExpandedTree),
                (TreeStr.managed_tree, ManagedTree),
                (TreeStr.flat_tree, FlatTree),
            ]
            for tree_str, tree_cls in tree_pairs:
                self.query_one(
                    self.tab_ids.tree_qid(tree_str), tree_cls
                ).unchanged = event.value
        elif event.switch.id == self.tab_ids.switch_id(Filters.expand_all):
            if event.value:
                self.query_one(
                    self.tab_ids.content_switcher_qid(Location.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.tab_ids.content_switcher_qid(Location.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(TreeStr.managed_tree)

    def action_toggle_filter_slider(self) -> None:
        self.query_one(
            self.tab_ids.filter_slider_qid, VerticalGroup
        ).toggle_class("-visible")


class ApplyTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.apply)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=Id.apply.tab_vertical_id(Location.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                tab_ids=Id.apply,
                buttons=(Buttons.tree_tab, Buttons.list_tab),
                location=Location.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.apply)

        with Vertical(id=Id.apply.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                tab_ids=Id.apply,
                buttons=(
                    Buttons.diff_tab,
                    Buttons.contents_tab,
                    Buttons.git_log_tab,
                ),
                location=Location.right,
            )
            with ContentSwitcher(
                id=Id.apply.content_switcher_id(Location.right),
                initial=Id.apply.view_id(ViewStr.diff_view),
            ):
                yield DiffView(
                    tab_name=Id.apply.tab_name,
                    view_id=Id.apply.view_id(ViewStr.diff_view),
                )
                yield ContentsView(
                    view_id=Id.apply.view_id(ViewStr.contents_view)
                )
                yield GitLogView(
                    view_id=Id.apply.view_id(ViewStr.git_log_view)
                )

        yield FilterSlider(
            tab_ids=Id.apply, filters=(Filters.unchanged, Filters.expand_all)
        )

    def on_mount(self) -> None:
        right_side = self.query_one(
            Id.apply.tab_vertical_qid(Location.right), Vertical
        )
        right_side.add_class(TcssStr.tab_right_vertical)
        right_side_content_switcher = self.query_one(
            Id.apply.content_switcher_qid(Location.right), ContentSwitcher
        )
        right_side_content_switcher.add_class(TcssStr.content_switcher_right)
        right_side_content_switcher.add_class(TcssStr.top_border_title)
        self.disable_buttons(
            (
                Buttons.apply_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        )


class ReAddTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.re_add)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=Id.re_add.tab_vertical_id(Location.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                tab_ids=Id.re_add,
                buttons=(Buttons.tree_tab, Buttons.list_tab),
                location=Location.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.re_add)

        with Vertical(id=Id.re_add.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                tab_ids=Id.re_add,
                buttons=(
                    Buttons.diff_tab,
                    Buttons.contents_tab,
                    Buttons.git_log_tab,
                ),
                location=Location.right,
            )

            with ContentSwitcher(
                id=Id.re_add.content_switcher_id(Location.right),
                initial=Id.re_add.view_id(ViewStr.diff_view),
            ):
                yield DiffView(
                    tab_name=Id.re_add.tab_name,
                    view_id=Id.re_add.view_id(ViewStr.diff_view),
                )
                yield ContentsView(
                    view_id=Id.re_add.view_id(ViewStr.contents_view)
                )
                yield GitLogView(
                    view_id=Id.re_add.view_id(ViewStr.git_log_view)
                )

        yield FilterSlider(
            tab_ids=Id.re_add, filters=(Filters.unchanged, Filters.expand_all)
        )

    def on_mount(self) -> None:
        self.query_one(
            Id.re_add.tab_vertical_qid(Location.right), Vertical
        ).add_class(TcssStr.tab_right_vertical)
        content_switcher_right = self.query_one(
            Id.re_add.content_switcher_qid(Location.right), ContentSwitcher
        )
        content_switcher_right.add_class(TcssStr.content_switcher_right)
        content_switcher_right.add_class(TcssStr.top_border_title)
        self.disable_buttons(
            (
                Buttons.re_add_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        )


class AddTab(OperateTabsBase):

    def __init__(self) -> None:
        super().__init__(tab_ids=Id.add)

    def compose(self) -> ComposeResult:
        with VerticalGroup(id=Id.add.tab_vertical_id(Location.left)):
            yield FilteredDirTree(
                CM_CFG.destDir,
                id=Id.add.tree_id(TreeStr.add_tree),
                classes=TcssStr.dir_tree_widget,
            )

        with Vertical(id=Id.add.tab_vertical_id(Location.right)):
            yield ContentsView(view_id=Id.add.view_id(ViewStr.contents_view))

        yield FilterSlider(
            tab_ids=Id.add, filters=(Filters.unmanaged_dirs, Filters.unwanted)
        )

    def on_mount(self) -> None:
        right_side = self.query_one(
            Id.add.tab_vertical_qid(Location.right), Vertical
        )
        right_side.border_title = str(CM_CFG.destDir)
        right_side.add_class(TcssStr.tab_right_vertical)
        right_side.add_class(TcssStr.top_border_title)
        left_side = self.query_one(
            Id.add.tab_vertical_qid(Location.left), VerticalGroup
        )
        left_side.border_title = str(CM_CFG.destDir)
        left_side.add_class(TcssStr.tab_left_vertical)
        left_side.add_class(TcssStr.top_border_title)

        tree = self.query_one(
            Id.add.tree_qid(TreeStr.add_tree), FilteredDirTree
        )
        tree.show_root = False
        tree.guide_depth = 3
        self.disable_buttons((Buttons.add_file_btn, Buttons.add_dir_btn))

    def on_directory_tree_file_selected(
        self, event: FilteredDirTree.FileSelected
    ) -> None:
        event.stop()

        assert event.node.data is not None
        self.query_one(
            Id.add.view_qid(ViewStr.contents_view), ContentsView
        ).path = event.node.data.path
        self.query_one(
            Id.add.tab_vertical_qid(Location.right), Vertical
        ).border_title = f"{event.node.data.path.relative_to(CM_CFG.destDir)}"
        self.enable_buttons((Buttons.add_file_btn,))

    def on_directory_tree_directory_selected(
        self, event: FilteredDirTree.DirectorySelected
    ) -> None:
        event.stop()
        assert event.node.data is not None
        self.query_one(
            Id.add.view_qid(ViewStr.contents_view), ContentsView
        ).path = event.node.data.path
        self.query_one(
            Id.add.tab_vertical_qid(Location.right), Vertical
        ).border_title = f"{event.node.data.path.relative_to(CM_CFG.destDir)}"
        self.disable_buttons((Buttons.add_file_btn,))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(
            Id.add.tree_qid(TreeStr.add_tree), FilteredDirTree
        )
        if event.switch.id == Id.add.switch_id(Filters.unmanaged_dirs):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == Id.add.switch_id(Filters.unwanted):
            tree.unwanted = event.value
        tree.reload()


class InitTab(Horizontal):

    def __init__(self) -> None:
        super().__init__(id=Id.init.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("[$success bold]chezmoi init[/]", markup=True)
            yield Static(
                "[$foreground-darken-1]not yet implemented[/]", markup=True
            )
            yield ButtonsHorizontal(
                tab_ids=Id.init,
                buttons=(
                    Buttons.new_repo_tab,
                    Buttons.clone_repo_tab,
                    Buttons.purge_repo_tab,
                ),
                location=Location.top,
            )
            with ContentSwitcher(
                id=Id.init.content_switcher_id(Location.top),
                initial=Id.init.view_id(ViewStr.init_new_view),
            ):
                yield InitNewRepo(tab_ids=Id.init)
                yield InitCloneRepo(tab_ids=Id.init)
                yield InitPurgeRepo(tab_ids=Id.init)

    def on_mount(self) -> None:
        buttons_horizontal = self.query_one(
            Id.init.buttons_horizontal_qid(Location.top), ButtonsHorizontal
        )
        buttons_horizontal.add_class(TcssStr.init_tab_buttons)
        buttons_horizontal.border_subtitle = " chezmoi init "

    @on(Button.Pressed)
    def set_content_switcher_current(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == Id.init.button_id(Buttons.new_repo_tab):
            self.query_one(
                Id.init.content_switcher_qid(Location.top), ContentSwitcher
            ).current = Id.init.view_id(ViewStr.init_new_view)

        elif event.button.id == Id.init.button_id(Buttons.clone_repo_tab):
            self.query_one(
                Id.init.content_switcher_qid(Location.top), ContentSwitcher
            ).current = Id.init.view_id(ViewStr.init_clone_view)

        elif event.button.id == Id.init.button_id(Buttons.purge_repo_tab):
            self.query_one(
                Id.init.content_switcher_qid(Location.top), ContentSwitcher
            ).current = Id.init.view_id(ViewStr.init_purge_view)


class DoctorTab(ScrollableContainer):

    def __init__(self) -> None:
        super().__init__(
            id=Id.doctor.tab_main_horizontal_id,
            classes=TcssStr.doctor_vertical,
        )
        self.dr_style = {
            "ok": theme.vars["text-success"],
            "info": theme.vars["foreground-darken-1"],
            "warning": theme.vars["text-warning"],
            "failed": theme.vars["text-error"],
            "error": theme.vars["text-error"],
        }

    def compose(self) -> ComposeResult:

        with Collapsible(title=DoctorEnum.doctor.value):
            yield DataTable[Text](
                id=ViewStr.doctor_table.name,
                classes=TcssStr.doctor_table,
                show_cursor=False,
            )
        yield Collapsible(
            Static(FLOW, classes=TcssStr.flow_diagram),
            title=DoctorEnum.diagram.value,
        )
        with Collapsible(title=DoctorEnum.doctor_template_data.value):
            yield Pretty(
                "placeholder", id=DoctorEnum.doctor_template_data.name
            )
        with Collapsible(title=DoctorEnum.cat_config.value):
            yield Pretty("placeholder", id=DoctorEnum.cat_config.name)
        with Collapsible(title=DoctorEnum.doctor_ignored.value):
            yield Pretty("placeholder", id=DoctorEnum.doctor_ignored.name)
        yield Collapsible(
            ListView(id=DoctorEnum.commands_not_found.name),
            title=DoctorEnum.commands_not_found.value,
        )

    def on_mount(self) -> None:
        for collapsible in self.query(Collapsible):
            collapsible.add_class(TcssStr.doctor_collapsible)

    def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
        event.stop()
        if event.collapsible.title == DoctorEnum.doctor.value:
            self.populate_doctor_data()
        elif event.collapsible.title == DoctorEnum.doctor_template_data.value:
            event.collapsible.query_one(
                DoctorEnum.doctor_template_data.qid, Pretty
            ).update(chezmoi.run.template_data())
        elif event.collapsible.title == DoctorEnum.cat_config.value:
            event.collapsible.query_one(
                DoctorEnum.cat_config.qid, Pretty
            ).update(chezmoi.run.cat_config())
        elif event.collapsible.title == DoctorEnum.doctor_ignored.value:
            event.collapsible.query_one(
                DoctorEnum.doctor_ignored.qid, Pretty
            ).update(chezmoi.run.ignored())

    def populate_doctor_data(self) -> None:
        doctor_table: DataTable[Text] = self.query_one(DataTable[Text])
        doctor_table.add_columns(*chezmoi.doctor.list_out[0].split())

        for line in chezmoi.doctor.list_out[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                self.populate_list_view_collapsible(row[1])
            elif row[0] in ["ok", "warning", "error", "failed"]:
                row = [
                    Text(cell_text, style=f"{self.dr_style[row[0]]}")
                    for cell_text in row
                ]
                doctor_table.add_row(*row)
            elif row[0] == "info" and row[2] == "not set":
                row = [
                    Text(cell_text, style=self.dr_style["warning"])
                    for cell_text in row
                ]
                doctor_table.add_row(*row)
            else:
                row = [Text(cell_text) for cell_text in row]
                doctor_table.add_row(*row)

    def populate_list_view_collapsible(self, row_var: str) -> None:
        list_view = self.query_exactly_one(ListView)
        if row_var in pw_mgr_info:
            list_view.append(
                ListItem(
                    Link(row_var, url=pw_mgr_info[row_var]["link"]),
                    Static(pw_mgr_info[row_var]["description"]),
                )
            )
        elif row_var not in pw_mgr_info:
            list_view.append(
                ListItem(
                    # color accent as that's how links are styled by default
                    Static(f"[$accent-muted]{row_var}[/]", markup=True),
                    Label("Not Found in $PATH."),
                )
            )
