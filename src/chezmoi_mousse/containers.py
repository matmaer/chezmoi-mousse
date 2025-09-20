"""Contains classes used as container components in main_tabs.py.

Rules:
- are only reused in the main_tabs.py module
- inherit from textual.containers classes
"""

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.widgets import Button, ContentSwitcher, Label, Switch

from chezmoi_mousse.constants import (
    Area,
    OperateBtn,
    TabBtn,
    TabName,
    TcssStr,
    TreeName,
    ViewName,
)
from chezmoi_mousse.id_typing import (
    AppType,
    OperateButtons,
    Switches,
    TabButtons,
    TabIds,
    VerticalButtons,
)
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    NodeData,
    TreeBase,
)


class OperateTabsBase(Horizontal, AppType):

    def __init__(self, *, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.current_path: Path = self.app.destDir
        super().__init__(id=self.tab_ids.tab_container_id)

    def disable_buttons(self, buttons_to_update: OperateButtons) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(
                self.tab_ids.button_id("#", btn=button_enum), Button
            )
            button.disabled = True
            if button_enum == OperateBtn.add_dir:
                button.tooltip = "not yet implemented"
                continue
            button.tooltip = "select a file to enable operations"

    def enable_buttons(self, buttons_to_update: OperateButtons) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(
                self.tab_ids.button_id("#", btn=button_enum), Button
            )
            if button_enum == OperateBtn.add_dir:
                button.tooltip = "not yet implemented"
                continue
            button.disabled = False
            button.tooltip = None

    def on_tree_node_selected(
        self, event: TreeBase.NodeSelected[NodeData]
    ) -> None:
        event.stop()
        assert event.node.data is not None
        if event.node.data.path == self.app.destDir:
            return
        self.current_path = event.node.data.path
        self.query_one(
            self.tab_ids.content_switcher_id("#", area=Area.right), Container
        ).border_title = f"{self.current_path.relative_to(self.app.destDir)}"
        current_view = self.query_one(
            self.tab_ids.content_switcher_id("#", area=Area.right),
            ContentSwitcher,
        ).current
        if current_view == self.tab_ids.view_id(view=ViewName.contents_view):
            self.query_exactly_one(ContentsView).path = self.current_path
        elif current_view == self.tab_ids.view_id(view=ViewName.diff_view):
            self.query_exactly_one(DiffView).path = self.current_path
        elif current_view == self.tab_ids.view_id(view=ViewName.git_log_view):
            self.query_exactly_one(GitLogView).path = self.current_path

        # Contents/Diff/GitLog Content Switcher
        # enable/disable operation buttons depending on selected node
        buttons_to_update: OperateButtons = ()
        if self.tab_ids.tab_name == TabName.apply_tab:
            buttons_to_update = (
                OperateBtn.apply_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
        elif self.tab_ids.tab_name == TabName.re_add_tab:
            buttons_to_update = (
                OperateBtn.re_add_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
        elif self.tab_ids.tab_name == TabName.add_tab:
            buttons_to_update = (OperateBtn.add_file, OperateBtn.add_dir)
        if event.node.allow_expand or current_view == self.tab_ids.view_id(
            view=ViewName.git_log_view
        ):
            self.disable_buttons(buttons_to_update)
        else:
            self.enable_buttons(buttons_to_update)

    @on(Button.Pressed, ".tab_button")
    def handle_tab_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        expand_all_switch = self.query_one(
            self.tab_ids.switch_id("#", switch=Switches.expand_all), Switch
        )
        # enable or disable expand all switch
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            expand_all_switch.disabled = False
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            expand_all_switch.disabled = True
        # Contents/Diff/GitLog Content Switcher
        # TODO only set the reactive var if the selected path in the Tree a
        # ctually changed
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.contents):
            self.query_exactly_one(ContentsView).path = self.current_path
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.diff):
            self.query_exactly_one(DiffView).path = self.current_path
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.git_log):
            self.query_exactly_one(GitLogView).path = self.current_path

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.tab_ids.switch_id(
            switch=Switches.unchanged
        ):
            tree_pairs: list[
                tuple[TreeName, type[ExpandedTree | ManagedTree | FlatTree]]
            ] = [
                (TreeName.expanded_tree, ExpandedTree),
                (TreeName.managed_tree, ManagedTree),
                (TreeName.flat_tree, FlatTree),
            ]
            for tree_str, tree_cls in tree_pairs:
                self.query_one(
                    self.tab_ids.tree_id("#", tree=tree_str), tree_cls
                ).unchanged = event.value
        elif event.switch.id == self.tab_ids.switch_id(
            switch=Switches.expand_all
        ):
            self.query_exactly_one(TreeContentSwitcher).expand_all_state = (
                event.value
            )
            if event.value:
                self.query_one(
                    self.tab_ids.content_switcher_id("#", area=Area.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(tree=TreeName.expanded_tree)
            else:
                self.query_one(
                    self.tab_ids.content_switcher_id("#", area=Area.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(tree=TreeName.managed_tree)

    def action_toggle_switch_slider(self) -> None:
        self.query_one(
            self.tab_ids.switches_slider_qid, VerticalGroup
        ).toggle_class("-visible")


class SwitchSlider(VerticalGroup):

    def __init__(
        self, *, tab_ids: TabIds, switches: tuple[Switches, Switches]
    ) -> None:
        self.switches = switches
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.switches_slider_id,
            classes=TcssStr.switches_vertical,
        )

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            with HorizontalGroup(
                id=self.tab_ids.switch_horizontal_id(switch=switch_enum),
                classes=TcssStr.switch_horizontal,
            ):
                yield Switch(
                    id=self.tab_ids.switch_id(switch=switch_enum), value=False
                )
                yield Label(
                    switch_enum.value.label, classes=TcssStr.switch_label
                ).with_tooltip(tooltip=switch_enum.value.tooltip)

    def on_mount(self) -> None:
        # add padding to the top switch horizontal group
        self.query_one(
            self.tab_ids.switch_horizontal_id("#", switch=self.switches[0]),
            HorizontalGroup,
        ).add_class(TcssStr.pad_bottom)


class ButtonsHorizontal(HorizontalGroup):

    def __init__(
        self,
        *,
        tab_ids: TabIds,
        buttons: TabButtons | OperateButtons,
        area: Area,
    ) -> None:
        self.buttons = buttons
        self.area: Area = area
        self.tab_ids: TabIds = tab_ids
        super().__init__(id=self.tab_ids.buttons_horizontal_id(self.area))

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.tab_ids.button_vertical_id(button_enum),
                classes=TcssStr.single_button_vertical,
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.tab_ids.button_id(btn=button_enum),
                )


class TabBtnHorizontal(ButtonsHorizontal):
    def __init__(self, *, tab_ids: TabIds, buttons: TabButtons, area: Area):
        super().__init__(tab_ids=tab_ids, buttons=buttons, area=area)

    def on_mount(self) -> None:
        self.add_class(TcssStr.tab_buttons_horizontal)
        self.query(Button).add_class(TcssStr.tab_button)
        self.query_one(
            self.tab_ids.button_id("#", btn=self.buttons[0])
        ).add_class(TcssStr.last_clicked)

    @on(Button.Pressed, ".tab_button")
    def update_tab_btn_last_clicked(self, event: Button.Pressed) -> None:
        self.query(Button).remove_class(TcssStr.last_clicked)
        event.button.add_class(TcssStr.last_clicked)


class OperateBtnHorizontal(ButtonsHorizontal):
    def __init__(self, *, tab_ids: TabIds, buttons: OperateButtons):
        super().__init__(tab_ids=tab_ids, buttons=buttons, area=Area.bottom)

    def on_mount(self) -> None:
        self.add_class(TcssStr.operate_buttons_horizontal)
        self.query(Button).add_class(TcssStr.operate_button)
        for button in self.query(Button):
            button.disabled = True


class OperateBtnContentSwitcher(ContentSwitcher, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids

        if self.tab_ids.tab_name == TabName.apply_tab:
            self.file_buttons: OperateButtons = (
                OperateBtn.apply_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )

            self.dir_buttons: OperateButtons = (
                OperateBtn.apply_dir,
                OperateBtn.forget_dir,
                OperateBtn.destroy_dir,
            )
        elif self.tab_ids.tab_name == TabName.re_add_tab:
            self.file_buttons: OperateButtons = (
                OperateBtn.re_add_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
            self.dir_buttons: OperateButtons = (
                OperateBtn.re_add_dir,
                OperateBtn.forget_dir,
                OperateBtn.destroy_dir,
            )

        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.bottom),
            initial=self.tab_ids.content_switcher_id(area=Area.bottom),
        )

    # TODO fix issue two widgets with same id
    def compose(self) -> ComposeResult:
        yield OperateBtnHorizontal(
            tab_ids=self.tab_ids, buttons=self.file_buttons
        )
        yield OperateBtnHorizontal(
            tab_ids=self.tab_ids, buttons=self.dir_buttons
        )


class ButtonsVertical(VerticalGroup):

    def __init__(
        self, *, tab_ids: TabIds, buttons: VerticalButtons, area: Area
    ) -> None:
        self.buttons: VerticalButtons = buttons
        self.area: Area = area
        self.tab_ids: TabIds = tab_ids
        super().__init__(
            id=self.tab_ids.buttons_vertical_group_id(self.area),
            classes=TcssStr.navigate_buttons_vertical,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield Button(
                label=button_enum.value,
                variant="primary",
                flat=True,
                classes=TcssStr.navigate_button,
                id=self.tab_ids.button_id(btn=button_enum),
            )


class TreeContentSwitcher(VerticalGroup, AppType):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        # updated by OperateTabsBase in on_switch_changed method
        self.expand_all_state: bool = False
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.left),
            classes=TcssStr.tab_left_vertical,
        )

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(
            tab_ids=self.tab_ids,
            buttons=(TabBtn.tree, TabBtn.list),
            area=Area.left,
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.left),
            initial=self.tab_ids.tree_id(tree=TreeName.managed_tree),
        ):
            yield ManagedTree(tab_ids=self.tab_ids)
            yield FlatTree(tab_ids=self.tab_ids)
            yield ExpandedTree(tab_ids=self.tab_ids)

    def on_mount(self) -> None:
        self.border_title = str(self.app.destDir)
        self.query_exactly_one(ContentSwitcher).add_class(
            TcssStr.content_switcher_left, TcssStr.border_title_top
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Tree/List Content Switcher
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            if self.expand_all_state:
                self.query_exactly_one(ContentSwitcher).current = (
                    self.tab_ids.tree_id(tree=TreeName.expanded_tree)
                )
            else:
                self.query_exactly_one(ContentSwitcher).current = (
                    self.tab_ids.tree_id(tree=TreeName.managed_tree)
                )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.tree_id(tree=TreeName.flat_tree)
            )


class ViewContentSwitcher(Vertical, AppType):
    def __init__(self, *, tab_ids: TabIds, diff_reverse: bool):
        self.tab_ids = tab_ids
        self.reverse = diff_reverse
        super().__init__(
            id=self.tab_ids.tab_vertical_id(area=Area.right),
            classes=TcssStr.tab_right_vertical,
        )

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(
            tab_ids=self.tab_ids,
            buttons=(TabBtn.diff, TabBtn.contents, TabBtn.git_log),
            area=Area.right,
        )
        with ContentSwitcher(
            id=self.tab_ids.content_switcher_id(area=Area.right),
            initial=self.tab_ids.view_id(view=ViewName.diff_view),
        ):
            yield DiffView(ids=self.tab_ids, reverse=self.reverse)
            yield ContentsView(ids=self.tab_ids)
            yield GitLogView(ids=self.tab_ids)

    def on_mount(self) -> None:
        self.query_one(ContentSwitcher).add_class(
            TcssStr.content_switcher_right, TcssStr.border_title_top
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.contents):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.view_id(view=ViewName.contents_view)
            )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.diff):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.view_id(view=ViewName.diff_view)
            )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.git_log):
            self.query_exactly_one(ContentSwitcher).current = (
                self.tab_ids.view_id(view=ViewName.git_log_view)
            )
