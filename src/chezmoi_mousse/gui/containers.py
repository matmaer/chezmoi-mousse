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

from chezmoi_mousse import (
    AreaName,
    OperateBtn,
    Switches,
    TabBtn,
    TabIds,
    Tcss,
    TreeName,
    ViewName,
)
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.button_groups import OperateBtnHorizontal
from chezmoi_mousse.gui.content_switchers import TreeSwitcher
from chezmoi_mousse.gui.messages import TreeNodeSelectedMsg
from chezmoi_mousse.gui.rich_logs import ContentsView, DiffView
from chezmoi_mousse.gui.widgets import (
    ExpandedTree,
    FlatTree,
    GitLogView,
    ManagedTree,
    OperateInfo,
)

__all__ = ["OperateTabsBase", "SwitchSlider"]


class OperateFullScreen(Container, AppType):

    def __init__(
        self,
        *,
        tab_ids: TabIds,
        path: Path,
        op_btn: OperateBtn,
        widget_to_show: DiffView | ContentsView,
    ) -> None:
        self.tab_ids = tab_ids
        self.op_btn = op_btn
        self.path = path
        self.widget_to_show = widget_to_show
        self.operation_cancelled: bool = True
        super().__init__(
            id=self.tab_ids.operate_container_id,
            classes=Tcss.operate_container.name,
        )

    def compose(self) -> ComposeResult:
        yield OperateInfo(operate_btn=self.op_btn)
        yield self.widget_to_show
        yield OperateBtnHorizontal(
            tab_ids=self.tab_ids,
            buttons=(self.op_btn, OperateBtn.operate_dismiss),
        )

    def on_mount(self) -> None:
        self.border_title = " Operation Info "
        self.border_subtitle = " escape key to close "
        operate_info = self.query_exactly_one(OperateInfo)
        operate_info.border_title = f" {self.path} "


class OperateTabsBase(Horizontal, AppType):

    def __init__(self, *, tab_ids: TabIds) -> None:
        self.current_path: Path | None = None
        self.tab_ids = tab_ids
        super().__init__(id=self.tab_ids.tab_container_id)
        self.diff_tab_btn = tab_ids.button_id(btn=TabBtn.diff)
        self.contents_tab_btn = tab_ids.button_id(btn=TabBtn.contents)
        self.git_log_tab_btn = tab_ids.button_id(btn=TabBtn.git_log)
        self.expand_all_state = False
        self.view_switcher_qid = self.tab_ids.content_switcher_id(
            "#", area=AreaName.right
        )
        self.tree_switcher_qid = self.tab_ids.content_switcher_id(
            "#", area=AreaName.left
        )

    def _update_view_path(self, path: Path) -> None:
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

    @on(TreeNodeSelectedMsg)
    def handle_tree_node_selected(self, event: TreeNodeSelectedMsg) -> None:
        selected_path = event.node_data.path
        self.query_one(
            self.view_switcher_qid, ContentSwitcher
        ).border_title = f"{selected_path}"
        self.current_path = selected_path
        self._update_view_path(selected_path)

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        # switch content and update view
        if event.button.id in (
            self.contents_tab_btn,
            self.diff_tab_btn,
            self.git_log_tab_btn,
        ):
            view_switcher = self.query_one(
                self.view_switcher_qid, ContentSwitcher
            )
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
            if self.current_path is None:
                self.current_path = self.app.destDir
            self._update_view_path(path=self.current_path)

        # toggle expand all switch enabled disabled state
        expand_all_switch = self.query_one(
            self.tab_ids.switch_id("#", switch=Switches.expand_all), Switch
        )
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            expand_all_switch.disabled = False
        elif event.button.id == self.tab_ids.button_id(btn=TabBtn.list):
            expand_all_switch.disabled = True

        # switch tree content view
        tree_switcher = self.query_one(self.tree_switcher_qid, ContentSwitcher)
        if event.button.id == self.tab_ids.button_id(btn=TabBtn.tree):
            if self.expand_all_state is True:
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
            if event.value is True:
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
                classes=Tcss.switch_horizontal.name,
            ):
                yield Switch(id=self.tab_ids.switch_id(switch=switch_enum))
                yield Label(
                    switch_enum.label, classes=Tcss.switch_label.name
                ).with_tooltip(tooltip=switch_enum.tooltip)

    def on_mount(self) -> None:
        # add padding to the top switch horizontal group
        self.query_one(
            self.tab_ids.switch_horizontal_id("#", switch=self.switches[0]),
            HorizontalGroup,
        ).add_class(Tcss.pad_bottom.name)
