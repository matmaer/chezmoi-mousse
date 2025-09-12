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
from textual.validation import URL
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Label,
    Select,
    Static,
    Switch,
)

from chezmoi_mousse.chezmoi import chezmoi_config, init_log
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
    Id,
    OperateButtons,
    Switches,
    TabButtons,
    TabIds,
)
from chezmoi_mousse.messages import InvalidInputMessage
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


class OperateTabsBase(Horizontal):

    def __init__(self, *, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.current_path: Path | None = None
        super().__init__(id=self.tab_ids.tab_name)

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
        self.current_path = event.node.data.path
        self.query_one(
            self.tab_ids.content_switcher_id("#", area=Area.right), Container
        ).border_title = (
            f"{self.current_path.relative_to(chezmoi_config.destDir)}"
        )
        current_view = self.query_one(
            self.tab_ids.content_switcher_id("#", area=Area.right),
            ContentSwitcher,
        ).current
        if current_view == self.tab_ids.view_id(view=ViewName.contents_view):
            self.query_one(
                self.tab_ids.view_id("#", view=ViewName.contents_view),
                ContentsView,
            ).path = self.current_path
        elif current_view == self.tab_ids.view_id(view=ViewName.diff_view):
            self.query_one(
                self.tab_ids.view_id("#", view=ViewName.diff_view), DiffView
            ).path = self.current_path
        elif current_view == self.tab_ids.view_id(view=ViewName.git_log_view):
            self.query_one(
                self.tab_ids.view_id("#", view=ViewName.git_log_view),
                GitLogView,
            ).path = self.current_path

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
        # Tree/List Content Switcher
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            expand_all_switch = self.query_one(
                self.tab_ids.switch_id("#", switch=Switches.expand_all), Switch
            )
            expand_all_switch.disabled = False
            if expand_all_switch.value:
                self.query_one(
                    self.tab_ids.content_switcher_id("#", area=Area.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(tree=TreeName.expanded_tree)
            else:
                self.query_one(
                    self.tab_ids.content_switcher_id("#", area=Area.left),
                    ContentSwitcher,
                ).current = self.tab_ids.tree_id(tree=TreeName.managed_tree)
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            self.query_one(
                self.tab_ids.switch_id("#", switch=Switches.expand_all), Switch
            ).disabled = True
            self.query_one(
                self.tab_ids.content_switcher_id("#", area=Area.left),
                ContentSwitcher,
            ).current = self.tab_ids.tree_id(tree=TreeName.flat_tree)
        # Contents/Diff/GitLog Content Switcher
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.contents):
            self.query_one(
                self.tab_ids.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(view=ViewName.contents_view)
            self.query_one(
                self.tab_ids.view_id("#", view=ViewName.contents_view),
                ContentsView,
            ).path = self.current_path
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.diff):
            self.query_one(
                self.tab_ids.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(view=ViewName.diff_view)
            self.query_one(
                self.tab_ids.view_id("#", view=ViewName.diff_view), DiffView
            ).path = self.current_path
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.git_log):
            self.query_one(
                self.tab_ids.content_switcher_id("#", area=Area.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(view=ViewName.git_log_view)
            self.query_one(
                self.tab_ids.view_id("#", view=ViewName.git_log_view),
                GitLogView,
            ).path = self.current_path
        # Init Content Switcher
        elif event.button.id == Id.init.button_id(btn=TabBtn.new_repo):
            self.query_one(
                Id.init.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            ).current = Id.init.view_id(view=ViewName.init_new_view)
        elif event.button.id == Id.init.button_id(btn=TabBtn.clone_repo):
            self.query_one(
                Id.init.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            ).current = Id.init.view_id(view=ViewName.init_clone_view)
        elif event.button.id == Id.init.button_id(btn=TabBtn.purge_repo):
            self.query_one(
                Id.init.content_switcher_id("#", area=Area.top),
                ContentSwitcher,
            ).current = Id.init.view_id(view=ViewName.init_purge_view)

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
        buttons: OperateButtons | TabButtons,
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

    def on_mount(self) -> None:
        if self.area == Area.bottom:
            self.add_operate_button_classes()
        else:
            self.add_tab_button_classes()

    def add_tab_button_classes(self) -> None:
        self.add_class(TcssStr.tab_buttons_horizontal)
        for button_enum in self.buttons:
            self.query_one(
                self.tab_ids.button_id("#", btn=button_enum)
            ).add_class(TcssStr.tab_button)
        self.query_one(
            self.tab_ids.button_id("#", btn=self.buttons[0])
        ).add_class(TcssStr.last_clicked)

    def add_operate_button_classes(self) -> None:
        self.add_class(TcssStr.operate_buttons_horizontal)
        for button_enum in self.buttons:
            button = self.query_one(
                self.tab_ids.button_id("#", btn=button_enum)
            )
            button.add_class(TcssStr.operate_button)

    @on(Button.Pressed, ".tab_button")
    def update_tab_btn_last_clicked(self, event: Button.Pressed) -> None:
        for button_enum in self.buttons:
            self.query_one(
                self.tab_ids.button_id("#", btn=button_enum)
            ).remove_class(TcssStr.last_clicked)
        event.button.add_class(TcssStr.last_clicked)


class TreeContentSwitcher(ContentSwitcher):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(area=Area.left),
            initial=self.tab_ids.tree_id(tree=TreeName.managed_tree),
        )

    def on_mount(self) -> None:
        self.border_title = str(chezmoi_config.destDir)
        self.add_class(TcssStr.content_switcher_left, TcssStr.border_title_top)

    def compose(self) -> ComposeResult:
        yield ManagedTree(tab_ids=self.tab_ids)
        yield FlatTree(tab_ids=self.tab_ids)
        yield ExpandedTree(tab_ids=self.tab_ids)


class InputHorizontal(HorizontalGroup):

    def compose(self) -> ComposeResult:
        with Vertical(classes=TcssStr.input_select_vertical):
            yield Select[str].from_values(
                ["https", "ssh"],
                classes=TcssStr.input_select,
                value="https",
                allow_blank=False,
                type_to_search=False,
            )
        with Vertical(classes=TcssStr.input_field_vertical):
            yield Input(
                placeholder="Enter repository URL",
                validate_on=["submitted"],
                validators=URL(),
                classes=TcssStr.input_field,
            )


class InitCloneRepo(Vertical):
    def __init__(self) -> None:
        super().__init__(id=Id.init.view_id(view=ViewName.init_clone_view))

    def compose(self) -> ComposeResult:
        yield Static(
            "Clone a remote chezmoi git repository and optionally apply"
        )
        # TODO: implement guess feature from chezmoi
        # TODO: add selection for https(with PAT token) or ssh
        yield InputHorizontal()

        with VerticalGroup(classes=TcssStr.operate_bottom_vertical_group):
            yield ButtonsHorizontal(
                tab_ids=Id.init,
                buttons=(OperateBtn.clone_repo,),
                area=Area.bottom,
            )
            yield init_log

    @on(Input.Submitted)
    def show_invalid_reasons(self, event: Input.Submitted) -> None:
        if (
            event.validation_result is not None
            and not event.validation_result.is_valid
        ):
            self.app.post_message(
                InvalidInputMessage(
                    reasons=event.validation_result.failure_descriptions
                )
            )


class InitPurgeRepo(Vertical):
    def __init__(self) -> None:
        super().__init__(id=Id.init.view_id(view=ViewName.init_purge_view))

    def compose(self) -> ComposeResult:
        yield Static(
            "Remove chezmoi's configuration, state, and source directory, but leave the target state intact."
        )
        yield ButtonsHorizontal(
            tab_ids=Id.init, buttons=(OperateBtn.purge_repo,), area=Area.bottom
        )
