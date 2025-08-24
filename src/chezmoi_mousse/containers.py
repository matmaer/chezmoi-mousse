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
    Static,
    Switch,
)

from chezmoi_mousse import CM_CFG
from chezmoi_mousse.id_typing import (
    Buttons,
    Id,
    Location,
    OperateBtn,
    OperateButtons,
    Switches,
    TabBtn,
    TabIds,
    TabStr,
    TcssStr,
    TreeStr,
    ViewStr,
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
        super().__init__(id=tab_ids.tab_name)

    def disable_buttons(self, buttons_to_update: OperateButtons) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(
                self.tab_ids.button_qid(button_enum), Button
            )
            button.disabled = True
            if button_enum == OperateBtn.add_dir:
                button.tooltip = "not yet implemented"
                continue
            button.tooltip = "select a file to enable operations"

    def enable_buttons(self, buttons_to_update: OperateButtons) -> None:
        for button_enum in buttons_to_update:
            button = self.app.query_one(
                self.tab_ids.button_qid(button_enum), Button
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
            self.tab_ids.content_switcher_qid(Location.right), Container
        ).border_title = f"{self.current_path.relative_to(CM_CFG.destDir)}"
        current_view = self.query_one(
            self.tab_ids.content_switcher_qid(Location.right), ContentSwitcher
        ).current
        if current_view == self.tab_ids.view_id(ViewStr.contents_view):
            self.query_one(
                self.tab_ids.view_qid(ViewStr.contents_view), ContentsView
            ).path = self.current_path
        elif current_view == self.tab_ids.view_id(ViewStr.diff_view):
            self.query_one(
                self.tab_ids.view_qid(ViewStr.diff_view), DiffView
            ).path = self.current_path
        elif current_view == self.tab_ids.view_id(ViewStr.git_log_view):
            self.query_one(
                self.tab_ids.view_qid(ViewStr.git_log_view), GitLogView
            ).path = self.current_path

        # enable/disable operation buttons depending on selected node
        buttons_to_update: OperateButtons = ()
        if self.tab_ids.tab_name == TabStr.apply_tab:
            buttons_to_update = (
                OperateBtn.apply_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
        elif self.tab_ids.tab_name == TabStr.re_add_tab:
            buttons_to_update = (
                OperateBtn.re_add_file,
                OperateBtn.forget_file,
                OperateBtn.destroy_file,
            )
        elif self.tab_ids.tab_name == TabStr.add_tab:
            buttons_to_update = (OperateBtn.add_file, OperateBtn.add_dir)
        if event.node.allow_expand or current_view == self.tab_ids.view_id(
            ViewStr.git_log_view
        ):
            self.disable_buttons(buttons_to_update)
        else:
            self.enable_buttons(buttons_to_update)

    @on(Button.Pressed, ".tab_button")
    def handle_tab_buttons(self, event: Button.Pressed) -> None:
        event.stop()
        # Tree/List Content Switcher
        if event.button.id == self.tab_ids.button_id(TabBtn.tree):
            expand_all_switch = self.query_one(
                self.tab_ids.switch_qid(Switches.expand_all), Switch
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
        elif event.button.id == self.tab_ids.button_id(TabBtn.list):
            self.query_one(
                self.tab_ids.switch_qid(Switches.expand_all), Switch
            ).disabled = True
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.left),
                ContentSwitcher,
            ).current = self.tab_ids.tree_id(TreeStr.flat_tree)
        # Contents/Diff/GitLog Content Switcher
        elif event.button.id == self.tab_ids.button_id(TabBtn.contents):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(ViewStr.contents_view)
            self.query_one(
                self.tab_ids.view_qid(ViewStr.contents_view), ContentsView
            ).path = self.current_path
        elif event.button.id == self.tab_ids.button_id(TabBtn.diff):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(ViewStr.diff_view)
            self.query_one(
                self.tab_ids.view_qid(ViewStr.diff_view), DiffView
            ).path = self.current_path
        elif event.button.id == self.tab_ids.button_id(TabBtn.git_log):
            self.query_one(
                self.tab_ids.content_switcher_qid(Location.right),
                ContentSwitcher,
            ).current = self.tab_ids.view_id(ViewStr.git_log_view)
            self.query_one(
                self.tab_ids.view_qid(ViewStr.git_log_view), GitLogView
            ).path = self.current_path
        # Init Content Switcher
        elif event.button.id == Id.init.button_id(TabBtn.new_repo):
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

    def on_switch_changed(self, event: Switch.Changed) -> None:
        event.stop()
        if event.switch.id == self.tab_ids.switch_id(Switches.unchanged):
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
        elif event.switch.id == self.tab_ids.switch_id(Switches.expand_all):
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

    def action_toggle_switch_slider(self) -> None:
        self.query_one(
            self.tab_ids.switches_slider_qid, VerticalGroup
        ).toggle_class("-visible")


class SwitchSlider(VerticalGroup):

    def __init__(
        self, *, tab_ids: TabIds, switches: tuple[Switches, Switches]
    ) -> None:
        self.switches = switches
        super().__init__(
            id=tab_ids.switches_slider_id, classes=TcssStr.switches_vertical
        )
        self.tab_ids = tab_ids

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            with HorizontalGroup(
                id=self.tab_ids.switch_horizontal_id(
                    switch_enum, Location.top
                ),
                classes=TcssStr.switch_horizontal,
            ):
                yield Switch(
                    id=self.tab_ids.switch_id(switch_enum), value=False
                )
                yield Label(
                    switch_enum.value.label, classes=TcssStr.switch_label
                ).with_tooltip(tooltip=switch_enum.value.tooltip)

    def on_mount(self) -> None:
        # add padding to the top switch horizontal group
        self.query_one(
            self.tab_ids.switch_horizontal_qid(self.switches[0], Location.top),
            HorizontalGroup,
        ).add_class(TcssStr.pad_bottom)


class ButtonsHorizontal(HorizontalGroup):

    def __init__(
        self, *, tab_ids: TabIds, buttons: Buttons, location: Location
    ) -> None:
        self.buttons = buttons
        self.location: Location = location
        self.tab_ids: TabIds = tab_ids
        super().__init__(
            id=tab_ids.buttons_horizontal_id(self.location),
            classes=TcssStr.tab_buttons_horizontal,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.tab_ids.button_vertical_id(button_enum),
                classes=TcssStr.single_button_vertical,
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.tab_ids.button_id(button_enum),
                )

    def on_mount(self) -> None:
        if self.location == Location.bottom:
            for button_enum in self.buttons:
                button = self.query_one(self.tab_ids.button_qid(button_enum))
                button.add_class(TcssStr.operate_button)
            return

        for button_enum in self.buttons:
            self.query_one(self.tab_ids.button_qid(button_enum)).add_class(
                TcssStr.tab_button
            )
        self.query_one(self.tab_ids.button_qid(self.buttons[0])).add_class(
            TcssStr.last_clicked
        )

    @on(Button.Pressed)
    def update_tab_btn_last_clicked(self, event: Button.Pressed) -> None:
        # tab buttons are never on location bottom
        if self.location == Location.bottom:
            return
        # update last_clicked class
        for button_enum in self.buttons:
            self.query_one(self.tab_ids.button_qid(button_enum)).remove_class(
                TcssStr.last_clicked
            )
        event.button.add_class(TcssStr.last_clicked)


class TreeContentSwitcher(ContentSwitcher):

    def __init__(self, tab_ids: TabIds):
        self.tab_ids = tab_ids
        super().__init__(
            id=self.tab_ids.content_switcher_id(Location.left),
            initial=self.tab_ids.tree_id(TreeStr.managed_tree),
        )

    def on_mount(self) -> None:
        self.border_title = str(CM_CFG.destDir)
        self.add_class(TcssStr.content_switcher_left, TcssStr.border_title_top)

    def compose(self) -> ComposeResult:
        yield ManagedTree(tab_ids=self.tab_ids)
        yield FlatTree(tab_ids=self.tab_ids)
        yield ExpandedTree(tab_ids=self.tab_ids)


class InitNewRepo(Vertical):
    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        super().__init__(id=self.tab_ids.view_id(ViewStr.init_new_view))

    def compose(self) -> ComposeResult:
        yield Label("Initialize a new chezmoi git repository")
        yield Input(placeholder="Enter config file path")
        yield ButtonsHorizontal(
            tab_ids=Id.init,
            buttons=(OperateBtn.new_repo,),
            location=Location.bottom,
        )


class InitCloneRepo(Vertical):
    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        super().__init__(id=self.tab_ids.view_id(ViewStr.init_clone_view))

    def compose(self) -> ComposeResult:
        yield Static(
            "Clone a remote chezmoi git repository and optionally apply"
        )
        # TODO: Use switch slider to add switches:
        # enable guess feature from chezmoi
        # clone and also apply
        yield Input(
            placeholder="Enter repository URL",
            validate_on=["submitted"],
            validators=URL(),
        )
        yield ButtonsHorizontal(
            tab_ids=Id.init,
            buttons=(OperateBtn.clone_repo,),
            location=Location.bottom,
        )

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
    def __init__(self, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        super().__init__(id=self.tab_ids.view_id(ViewStr.init_purge_view))

    def compose(self) -> ComposeResult:
        yield Static(
            "Remove chezmoi's configuration, state, and source directory, but leave the target state intact."
        )
        yield ButtonsHorizontal(
            tab_ids=Id.init,
            buttons=(OperateBtn.purge_repo,),
            location=Location.bottom,
        )
