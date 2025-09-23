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
    VerticalGroup,
)
from textual.widgets import Button, ContentSwitcher, Label, Switch

from chezmoi_mousse.constants import (
    Area,
    OperateBtn,
    TabBtn,
    TcssStr,
    TreeName,
    ViewName,
)
from chezmoi_mousse.content_switchers import TreeSwitcher
from chezmoi_mousse.id_typing import AppType, OperateButtons, Switches, TabIds
from chezmoi_mousse.messages import TreeNodeDataMsg
from chezmoi_mousse.widgets import (
    ContentsView,
    DiffView,
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
)


class OperateTabsBase(Horizontal, AppType):

    def __init__(self, *, tab_ids: TabIds) -> None:
        self.tab_ids = tab_ids
        self.tab_name = tab_ids.tab_name
        self.current_path: Path | None = None
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

    def update_view_path(self, path: Path) -> None:
        current_view_id = self.query_one(
            self.tab_ids.content_switcher_id("#", area=Area.right),
            ContentSwitcher,
        ).current
        if current_view_id == self.tab_ids.view_id(
            view=ViewName.contents_view
        ):
            self.query_exactly_one(ContentsView).path = path
        elif current_view_id == self.tab_ids.view_id(view=ViewName.diff_view):
            self.query_exactly_one(DiffView).path = path
        elif current_view_id == self.tab_ids.view_id(
            view=ViewName.git_log_view
        ):
            self.query_exactly_one(GitLogView).path = path

    @on(TreeNodeDataMsg)
    def handle_tree_node_selected(self, event: TreeNodeDataMsg) -> None:
        event.stop()
        selected_path = event.node_context.node_data.path
        self.query_one(
            self.tab_ids.content_switcher_id("#", area=Area.right), Container
        ).border_title = f"{selected_path.relative_to(self.app.destDir)}"
        self.current_path = selected_path
        self.update_view_path(selected_path)

    @on(Button.Pressed, ".tab_button")
    def handle_expand_all_switch(self, event: Button.Pressed) -> None:
        switch_id = self.tab_ids.switch_id("#", switch=Switches.expand_all)
        expand_all_switch = self.query_one(switch_id, Switch)
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            expand_all_switch.disabled = False
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            expand_all_switch.disabled = True

    @on(Button.Pressed, ".tab_button")
    def maybe_update_view_path(self, event: Button.Pressed) -> None:
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.contents):
            view_path = self.query_exactly_one(ContentsView).path
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.diff):
            view_path = self.query_exactly_one(DiffView).path
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.git_log):
            view_path = self.query_exactly_one(GitLogView).path
        else:
            return
        if self.current_path is None or view_path is None:
            self.current_path = self.app.destDir
        if view_path != self.current_path:
            self.update_view_path(self.current_path)

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
            self.query_exactly_one(TreeSwitcher).expand_all_state = event.value
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
