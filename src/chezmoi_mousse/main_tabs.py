from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import (
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
    OperateTabsBase,
    TreeContentSwitcher,
)
from chezmoi_mousse.id_typing import (
    DoctorEnum,
    Filters,
    Id,
    Location,
    OperateBtn,
    TabBtn,
    TcssStr,
    TreeStr,
    ViewStr,
)
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    FilteredDirTree,
    GitLogView,
)


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
                buttons=(TabBtn.tree, TabBtn.list),
                location=Location.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.apply)

        with Vertical(id=Id.apply.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                tab_ids=Id.apply,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
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
        self.query_one(
            Id.apply.content_switcher_qid(Location.right), ContentSwitcher
        ).add_class(TcssStr.content_switcher_right, TcssStr.border_title_top)
        self.disable_buttons(
            (
                OperateBtn.apply_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
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
                buttons=(TabBtn.tree, TabBtn.list),
                location=Location.left,
            )
            yield TreeContentSwitcher(tab_ids=Id.re_add)

        with Vertical(id=Id.re_add.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                tab_ids=Id.re_add,
                buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
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
        self.query_one(
            Id.re_add.content_switcher_qid(Location.right), ContentSwitcher
        ).add_class(TcssStr.content_switcher_right, TcssStr.border_title_top)
        self.disable_buttons(
            (
                OperateBtn.re_add_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
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
        right_side.add_class(
            TcssStr.tab_right_vertical, TcssStr.border_title_top
        )
        left_side = self.query_one(
            Id.add.tab_vertical_qid(Location.left), VerticalGroup
        )
        left_side.border_title = str(CM_CFG.destDir)
        left_side.add_class(
            TcssStr.tab_left_vertical, TcssStr.border_title_top
        )

        tree = self.query_one(
            Id.add.tree_qid(TreeStr.add_tree), FilteredDirTree
        )
        tree.show_root = False
        tree.guide_depth = 3
        self.disable_buttons((OperateBtn.add_file, OperateBtn.add_dir))

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
        self.enable_buttons((OperateBtn.add_file,))

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
        self.disable_buttons((OperateBtn.add_file,))

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
                    TabBtn.clone_repo,
                    TabBtn.new_repo,
                    TabBtn.purge_repo,
                ),
                location=Location.top,
            )
            with ContentSwitcher(
                id=Id.init.content_switcher_id(Location.top),
                initial=Id.init.view_id(ViewStr.init_clone_view),
            ):
                yield InitCloneRepo(tab_ids=Id.init)
                yield InitNewRepo(tab_ids=Id.init)
                yield InitPurgeRepo(tab_ids=Id.init)

    def on_mount(self) -> None:
        buttons_horizontal = self.query_one(
            Id.init.buttons_horizontal_qid(Location.top), ButtonsHorizontal
        )
        buttons_horizontal.add_class(TcssStr.border_title_bottom)
        buttons_horizontal.border_subtitle = " chezmoi init "

    @on(Button.Pressed)
    def handle_init_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == Id.init.button_id(TabBtn.new_repo):
            self.query_one(
                Id.init.content_switcher_qid(Location.top), ContentSwitcher
            ).current = Id.init.view_id(ViewStr.init_new_view)

        elif event.button.id == Id.init.button_id(TabBtn.clone_repo):
            self.query_one(
                Id.init.content_switcher_qid(Location.top), ContentSwitcher
            ).current = Id.init.view_id(ViewStr.init_clone_view)

        elif event.button.id == Id.init.button_id(TabBtn.purge_repo):
            self.query_one(
                Id.init.content_switcher_qid(Location.top), ContentSwitcher
            ).current = Id.init.view_id(ViewStr.init_purge_view)
        elif event.button.id == Id.init.button_id(OperateBtn.clone_repo):
            self.notify("Clone repository button pressed")
        elif event.button.id == Id.init.button_id(OperateBtn.new_repo):
            self.notify("New repository button pressed")
        elif event.button.id == Id.init.button_id(OperateBtn.purge_repo):
            self.notify("Purge repository button pressed")


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
