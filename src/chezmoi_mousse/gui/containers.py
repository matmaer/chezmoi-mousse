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
        super().__init__(id=self.tab_ids.tab_container_id)

    def _update_view_path(self) -> None:
        contents_view = self.query_exactly_one(ContentsView)
        if contents_view.path != self.current_path:
            contents_view.path = self.current_path
            contents_view.border_title = f" {self.current_path} "

        diff_view = self.query_exactly_one(DiffView)
        if diff_view.path != self.current_path:
            diff_view.path = self.current_path
            diff_view.border_title = f" {self.current_path} "

        git_log_view = self.query_exactly_one(GitLogView)
        if git_log_view.path != self.current_path:
            git_log_view.path = self.current_path
            git_log_view.border_title = f" {self.current_path} "

    @on(TreeNodeSelectedMsg)
    def update_current_path(self, event: TreeNodeSelectedMsg) -> None:
        self.current_path = event.node_data.path
        self._update_view_path()

    @on(Button.Pressed, Tcss.tab_button.value)
    def handle_tab_button_pressed(self, event: Button.Pressed) -> None:
        # switch content and update view path if needed
        if event.button.id in (
            self.contents_tab_btn,
            self.diff_tab_btn,
            self.git_log_tab_btn,
        ):
            self._update_view_path()
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

        # toggle expand all switch enabled disabled state
        expand_all_switch = self.query_one(
            self.tab_ids.switch_id("#", switch=Switches.expand_all.value),
            Switch,
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
            switch=Switches.unchanged.value
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
            switch=Switches.expand_all.value
        ):
            self.expand_all_state = event.value
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
        for switch_data in self.switches:
            with HorizontalGroup(
                id=self.tab_ids.switch_horizontal_id(switch=switch_data.value),
                classes=Tcss.switch_horizontal.name,
            ):
                yield Switch(
                    id=self.tab_ids.switch_id(switch=switch_data.value)
                )
                yield Label(
                    switch_data.value.label, classes=Tcss.switch_label.name
                ).with_tooltip(tooltip=switch_data.value.tooltip)

    def on_mount(self) -> None:
        # add padding to the top switch horizontal group
        self.query_one(
            self.tab_ids.switch_horizontal_id(
                "#", switch=self.switches[0].value
            ),
            HorizontalGroup,
        ).add_class(Tcss.pad_bottom.name)
