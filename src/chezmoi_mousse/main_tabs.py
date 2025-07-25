from pathlib import Path
from typing import cast

from rich.text import Text
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
    TreeContentSwitcher,
)
from chezmoi_mousse.id_typing import (
    Buttons,
    Filters,
    IdMixin,
    Location,
    PrettyIdEnum,
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


class OperateTabsBase(Horizontal, IdMixin):

    def __init__(self, tab_name: TabStr) -> None:
        IdMixin.__init__(self, tab_name)
        super().__init__(id=self.tab_main_horizontal_id)

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

    def disable_buttons(self, buttons_to_update: tuple[Buttons, ...]) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(self.button_qid(button_enum), Button)
            button.disabled = True
            if button_enum == Buttons.add_dir_btn:
                button.tooltip = "not yet implemented"
                continue
            button.tooltip = "select a file to enable operations"

    def enable_buttons(self, buttons_to_update: tuple[Buttons, ...]) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(self.button_qid(button_enum), Button)
            if button_enum == Buttons.add_dir_btn:
                button.tooltip = "not yet implemented"
                continue
            button.disabled = False
            button.tooltip = None

    def on_tree_node_selected(
        self, event: TreeBase.NodeSelected[NodeData]
    ) -> None:
        assert event.node.data is not None
        self.update_right_side_content_switcher(event.node.data.path)

        buttons_to_update: tuple[Buttons, ...] = ()
        if self.tab_name == TabStr.apply_tab:
            buttons_to_update = (
                Buttons.apply_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        elif self.tab_name == TabStr.re_add_tab:
            buttons_to_update = (
                Buttons.re_add_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        elif self.tab_name == TabStr.add_tab:
            buttons_to_update = (Buttons.add_file_btn, Buttons.add_dir_btn)
        else:
            return
        if event.node.allow_expand:
            self.disable_buttons(buttons_to_update)
        else:
            self.enable_buttons(buttons_to_update)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Tree/List Switch
        if event.button.id == self.button_id(Buttons.tree_btn):
            expand_all_switch = self.query_one(
                self.switch_qid(Filters.expand_all), Switch
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
        elif event.button.id == self.button_id(Buttons.list_btn):
            self.query_one(
                self.content_switcher_qid(Location.left), ContentSwitcher
            ).current = self.tree_id(TreeStr.flat_tree)
            self.query_one(
                self.switch_qid(Filters.expand_all), Switch
            ).disabled = True
        # Contents/Diff/GitLog Switch
        elif event.button.id == self.button_id(Buttons.contents_btn):
            self.query_one(
                self.content_switcher_qid(Location.right), ContentSwitcher
            ).current = self.view_id(ViewStr.contents_view)

        elif event.button.id == self.button_id(Buttons.diff_btn):
            self.query_one(
                self.content_switcher_qid(Location.right), ContentSwitcher
            ).current = self.view_id(ViewStr.diff_view)

        elif event.button.id == self.button_id(Buttons.git_log_btn):
            self.query_one(
                self.content_switcher_qid(Location.right), ContentSwitcher
            ).current = self.view_id(ViewStr.git_log_view)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.switch_id(Filters.unchanged):
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
        elif event.switch.id == self.switch_id(Filters.expand_all):
            if event.value:
                self.query_one(
                    self.content_switcher_qid(Location.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.expanded_tree)
            else:
                self.query_one(
                    self.content_switcher_qid(Location.left), ContentSwitcher
                ).current = self.tree_id(TreeStr.managed_tree)

    def action_toggle_filter_slider(self) -> None:
        self.query_one(self.filter_slider_qid, VerticalGroup).toggle_class(
            "-visible"
        )


class ApplyTab(OperateTabsBase):

    def __init__(self, tab_name: TabStr) -> None:
        super().__init__(tab_name)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(Location.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                self.tab_name,
                buttons=(Buttons.tree_btn, Buttons.list_btn),
                location=Location.left,
            )
            yield TreeContentSwitcher(self.tab_name)

        with Vertical(id=self.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                self.tab_name,
                buttons=(
                    Buttons.diff_btn,
                    Buttons.contents_btn,
                    Buttons.git_log_btn,
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
            self.tab_name, filters=(Filters.unchanged, Filters.expand_all)
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
        self.disable_buttons(
            (
                Buttons.apply_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        )


class ReAddTab(OperateTabsBase):

    def __init__(self, tab_name: TabStr) -> None:
        super().__init__(tab_name)

    def compose(self) -> ComposeResult:
        with VerticalGroup(
            id=self.tab_vertical_id(Location.left),
            classes=TcssStr.tab_left_vertical,
        ):
            yield ButtonsHorizontal(
                self.tab_name,
                buttons=(Buttons.tree_btn, Buttons.list_btn),
                location=Location.left,
            )
            yield TreeContentSwitcher(self.tab_name)

        with Vertical(id=self.tab_vertical_id(Location.right)):
            yield ButtonsHorizontal(
                self.tab_name,
                buttons=(
                    Buttons.diff_btn,
                    Buttons.contents_btn,
                    Buttons.git_log_btn,
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
            self.tab_name, filters=(Filters.unchanged, Filters.expand_all)
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
        self.disable_buttons(
            (
                Buttons.re_add_file_btn,
                Buttons.forget_file_btn,
                Buttons.destroy_file_btn,
            )
        )


class AddTab(OperateTabsBase):

    def __init__(self, tab_name: TabStr) -> None:
        super().__init__(tab_name)

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
            self.tab_name, filters=(Filters.unmanaged_dirs, Filters.unwanted)
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
        self.disable_buttons((Buttons.add_file_btn, Buttons.add_dir_btn))

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
        self.enable_buttons((Buttons.add_file_btn,))

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
        self.disable_buttons((Buttons.add_file_btn,))

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        tree = self.query_one(self.tree_qid(TreeStr.add_tree), FilteredDirTree)
        if event.switch.id == self.switch_id(Filters.unmanaged_dirs):
            tree.unmanaged_dirs = event.value
        elif event.switch.id == self.switch_id(Filters.unwanted):
            tree.unwanted = event.value
        tree.reload()


class InitTab(Horizontal, IdMixin):

    def __init__(self, tab_name: TabStr) -> None:
        IdMixin.__init__(self, tab_name)
        super().__init__(id=self.tab_main_horizontal_id)

    def compose(self) -> ComposeResult:
        yield Static(
            "[$success bold]chezmoi init[/]\n[$text-disabled]not yet implemented[/]",
            markup=True,
        )


class DoctorTab(ScrollableContainer, IdMixin):

    def __init__(self, tab_name: TabStr) -> None:
        IdMixin.__init__(self, tab_name)
        super().__init__(
            id=self.tab_main_horizontal_id, classes=TcssStr.doctor_vertical
        )
        self.dr_style = {
            "ok": theme.vars["text-success"],
            "warning": theme.vars["text-warning"],
            "error": theme.vars["text-error"],
            "info": theme.vars["foreground-darken-1"],
        }

    def compose(self) -> ComposeResult:

        with Collapsible(title="chezmoi doctor output"):
            yield DataTable[Text](
                id=ViewStr.doctor_table.name,
                classes=TcssStr.doctor_table,
                show_cursor=False,
            )
        yield Collapsible(
            Static(FLOW, classes=TcssStr.flow_diagram), title="chezmoi diagram"
        )
        with Collapsible(title=PrettyIdEnum.doctor_template_data.value):
            yield Pretty(
                "placeholder", id=PrettyIdEnum.doctor_template_data.name
            )
        with Collapsible(title=PrettyIdEnum.doctor_cat_config.value):
            yield Pretty("placeholder", id=PrettyIdEnum.doctor_cat_config.name)
        with Collapsible(title=PrettyIdEnum.doctor_ignored.value):
            yield Pretty("placeholder", id=PrettyIdEnum.doctor_ignored.name)
        yield Collapsible(ListView(), title="Commands Not Found")

    def on_mount(self) -> None:
        for collapsible in self.query(Collapsible):
            collapsible.add_class(TcssStr.doctor_collapsible)

    def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
        event.stop()
        if event.collapsible.title == PrettyIdEnum.doctor_template_data.value:
            event.collapsible.query_one(
                PrettyIdEnum.doctor_template_data.qid, Pretty
            ).update(chezmoi.run.template_data())
        elif event.collapsible.title == PrettyIdEnum.doctor_cat_config.value:
            event.collapsible.query_one(
                PrettyIdEnum.doctor_cat_config.qid, Pretty
            ).update(chezmoi.run.cat_config())
        elif event.collapsible.title == PrettyIdEnum.doctor_ignored.value:
            event.collapsible.query_one(
                PrettyIdEnum.doctor_ignored.qid, Pretty
            ).update(chezmoi.run.ignored())

    # do not put this in the on_mount method as textual manages this
    def populate_doctor_data(self) -> None:
        # cast datatype as there's no other way because we have to handle
        # non generic type and a subscribed type for runtime and type checking
        doctor_table = cast(
            DataTable[Text],
            self.get_widget_by_id(ViewStr.doctor_table.name, DataTable),
        )
        doctor_table.add_columns(*chezmoi.doctor.list_out[0].split())

        for line in chezmoi.doctor.list_out[1:]:
            row = tuple(line.split(maxsplit=2))
            if row[0] == "info" and "not found in $PATH" in row[2]:
                self.populate_list_view_collapsible(row[1])
            elif row[0] == "ok" or row[0] == "warning" or row[0] == "error":
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
