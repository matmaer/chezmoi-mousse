"""Contains classes used as container components in main_tabs.py.

Rules:
- are only reused in the main_tabs.py module
- inherit from textual.containers classes
"""

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, VerticalGroup
from textual.widgets import Button, ContentSwitcher, Label, Switch

from chezmoi_mousse.content_switchers import TreeSwitcher
from chezmoi_mousse.id_typing import (
    AppType,
    Area,
    Switches,
    TabBtn,
    TabIds,
    TabName,
    Tcss,
    TreeName,
    ViewName,
)
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
        self.current_path: Path | None = None
        self.tab_ids = tab_ids
        self.tab_name = self.tab_ids.tab_name
        self.expand_all_state = False
        self.view_switcher_id = self.tab_ids.content_switcher_id(
            area=Area.right
        )
        self.view_switcher_qid = self.tab_ids.content_switcher_id(
            "#", area=Area.right
        )
        self.tree_switcher_id = self.tab_ids.content_switcher_id(
            area=Area.left
        )
        self.tree_switcher_qid = self.tab_ids.content_switcher_id(
            "#", area=Area.left
        )
        self.diff_tab_btn = tab_ids.button_id(btn=TabBtn.diff)
        self.contents_tab_btn = tab_ids.button_id(btn=TabBtn.contents)
        self.git_log_tab_btn = tab_ids.button_id(btn=TabBtn.git_log)
        super().__init__(id=self.tab_ids.tab_container_id)

    def on_mount(self) -> None:
        if self.tab_name in (TabName.apply_tab, TabName.re_add_tab):
            self.query_one(
                self.view_switcher_qid, ContentSwitcher
            ).border_title = str(self.app.destDir)
            self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            ).border_title = str(self.app.destDir)
            self.query_one(self.tree_switcher_qid, ContentSwitcher).add_class(
                Tcss.border_title_top
            )

    def update_view_path(self, path: Path) -> None:
        current_view_id = self.query_one(
            self.view_switcher_qid, ContentSwitcher
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

    def maybe_update_view_path(self, event: Button.Pressed) -> None:
        if event.button.id == self.contents_tab_btn:
            view_path = self.query_exactly_one(ContentsView).path
        elif event.button.id == self.diff_tab_btn:
            view_path = self.query_exactly_one(DiffView).path
        elif event.button.id == self.git_log_tab_btn:
            view_path = self.query_exactly_one(GitLogView).path
        else:
            return
        if self.current_path is None or view_path is None:
            self.current_path = self.app.destDir
        if view_path != self.current_path:
            self.update_view_path(self.current_path)

    @on(TreeNodeDataMsg)
    def handle_tree_node_selected(self, event: TreeNodeDataMsg) -> None:
        selected_path = event.node_context.node_data.path
        self.query_one(
            self.view_switcher_qid, ContentSwitcher
        ).border_title = f"{selected_path.relative_to(self.app.destDir)}"
        self.current_path = selected_path
        self.update_view_path(selected_path)

    @on(Button.Pressed, f".{Tcss.tab_button}")
    def toggle_expand_all_switch_enabled_disabled_state(
        self, event: Button.Pressed
    ) -> None:
        expand_all_switch = self.query_one(
            self.tab_ids.switch_id("#", switch=Switches.expand_all), Switch
        )
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            expand_all_switch.disabled = False
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            expand_all_switch.disabled = True

    @on(Button.Pressed, f".{Tcss.tab_button}")
    def switch_content_and_update_view(self, event: Button.Pressed) -> None:
        view_switcher = self.query_one(self.view_switcher_qid, ContentSwitcher)
        if event.button.id == self.contents_tab_btn:
            view_switcher.current = self.tab_ids.view_id(
                view=ViewName.contents_view
            )
        elif event.button.id == self.diff_tab_btn:
            view_switcher.current = self.tab_ids.view_id(
                view=ViewName.diff_view
            )
        elif event.button.id == self.git_log_tab_btn:
            view_switcher.current = self.tab_ids.view_id(
                view=ViewName.git_log_view
            )
        self.maybe_update_view_path(event=event)

    @on(Button.Pressed, f".{Tcss.tab_button}")
    def switch_tree_content_view(self, event: Button.Pressed) -> None:
        tree_switcher = self.query_one(self.tree_switcher_qid, ContentSwitcher)
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            if self.expand_all_state:
                tree_switcher.current = self.tab_ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.tab_ids.tree_id(
                    tree=TreeName.managed_tree
                )
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            tree_switcher.current = self.tab_ids.tree_id(
                tree=TreeName.flat_tree
            )

    @on(Switch.Changed)
    def handle_tree_filter_switches(self, event: Switch.Changed) -> None:
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
            self.expand_all_state = event.value
            self.query_exactly_one(TreeSwitcher).expand_all_state = event.value
            tree_switcher = self.query_one(
                self.tree_switcher_qid, ContentSwitcher
            )
            if event.value:
                tree_switcher.current = self.tab_ids.tree_id(
                    tree=TreeName.expanded_tree
                )
            else:
                tree_switcher.current = self.tab_ids.tree_id(
                    tree=TreeName.managed_tree
                )

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
        super().__init__(id=self.tab_ids.switches_slider_id)

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            with HorizontalGroup(
                id=self.tab_ids.switch_horizontal_id(switch=switch_enum),
                classes=Tcss.switch_horizontal,
            ):
                yield Switch(id=self.tab_ids.switch_id(switch=switch_enum))
                yield Label(
                    switch_enum.value.label, classes=Tcss.switch_label
                ).with_tooltip(tooltip=switch_enum.value.tooltip)

    def on_mount(self) -> None:
        # add padding to the top switch horizontal group
        self.query_one(
            self.tab_ids.switch_horizontal_id("#", switch=self.switches[0]),
            HorizontalGroup,
        ).add_class(Tcss.pad_bottom)
