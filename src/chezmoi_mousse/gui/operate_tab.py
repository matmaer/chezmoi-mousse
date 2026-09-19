from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.widgets import (
    Label,
    RadioButton,
    RadioSet,
    Switch,
    TabPane,
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.actionables import (
    DestDirBtn,
    OperateBtnGroup,
    RefreshBtn,
)
from chezmoi_mousse.gui.common.labeled_views import ContentsView, GitLogView
from chezmoi_mousse.gui.common.managed_trees import (
    ManagedTree,
    ManagedTreeExpanded,
    StatusTree,
    StatusTreeExpanded,
    UnManagedTree,
    UnManagedTreeExpanded,
    UnWantedTree,
    UnWantedTreeExpanded,
)
from chezmoi_mousse.gui.common.messages import (
    DestDirBtnMsg,
    SwitchGroupMsg,
)
from chezmoi_mousse.named_tuples import SwitchStates
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["OperateTab"]


class LeftSideVertical(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, *, ids: AppIds) -> None:
        self.ids = ids
        super().__init__(id=ids.container.left_side, classes=Tcss.operations_left)

    def compose(self) -> ComposeResult:
        yield DestDirBtn(app_ids=self.ids)
        yield StatusTree()
        yield ManagedTree()
        yield UnManagedTree()
        yield UnWantedTree()
        yield ManagedTreeExpanded()
        yield StatusTreeExpanded()
        yield UnManagedTreeExpanded()
        yield UnWantedTreeExpanded()

    @on(DestDirBtnMsg)
    def handle_dest_dir_btn_msg(self, msg: DestDirBtnMsg) -> None:
        self.notify(f"DestDirBtn pressed: {msg.tab_label}")


class SwitchGroup(VerticalGroup):
    def __init__(self, *, ids: AppIds) -> None:
        self.ids = ids
        self.switch_labels = (
            LabelStr.expand_all,
            LabelStr.show_unchanged,
            LabelStr.show_unmanaged,
            LabelStr.show_unwanted,
        )
        super().__init__(classes=Tcss.switches_vert_group)

    def compose(self) -> ComposeResult:
        for switch_label in self.switch_labels:
            yield HorizontalGroup(
                Switch(id=self.ids.switch_id(switch_label=switch_label)),
                Label(switch_label),
                classes=Tcss.switch_with_label,
            )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        expand_all_switch = self.query_one(self.ids.switch.expand_all_q, Switch)
        unchanged_switch = self.query_one(self.ids.switch.show_unchanged_q, Switch)
        unmanaged_switch = self.query_one(self.ids.switch.show_unmanaged_q, Switch)
        unwanted_switch = self.query_one(self.ids.switch.show_unwanted_q, Switch)

        switch_states: SwitchStates = SwitchStates(
            expand_all=expand_all_switch.value,
            show_unchanged=unchanged_switch.value,
            show_unmanaged=unmanaged_switch.value,
            show_unwanted=unwanted_switch.value,
        )
        self.post_message(SwitchGroupMsg(switch_states=switch_states))


class RightSideVertical(Vertical):
    def __init__(
        self,
        *,
        ids: AppIds,
        radio_labels: tuple[LabelStr, ...],
    ) -> None:
        self.ids = ids
        self.radio_labels = radio_labels
        super().__init__(id=ids.container.right_side, classes=Tcss.operations_right)

    def compose(self) -> ComposeResult:
        with RadioSet():
            for radio_label in self.radio_labels:
                yield RadioButton(radio_label, compact=True)
        yield SwitchGroup(ids=self.ids)
        yield RefreshBtn(app_ids=self.ids)

    def on_mount(self) -> None:
        first_radio = self.query_one(RadioSet).query(RadioButton).first()
        if first_radio:
            first_radio.value = True


class OperateTab(TabPane):
    def __init__(self) -> None:
        self.ids = store.operate_ids
        super().__init__(
            id=BtnLabel.operate.pane_id,
            title=BtnLabel.operate,
        )

    def compose(self) -> ComposeResult:
        with Horizontal(classes=Tcss.operate_pane):
            yield LeftSideVertical(ids=self.ids)
            yield GitLogView(ids=self.ids, classes=Tcss.operations_middle)
            yield ContentsView(ids=self.ids, classes=Tcss.operations_middle)
            yield RightSideVertical(
                ids=self.ids,
                radio_labels=(
                    LabelStr.radio_git_log,
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                ),
            )
            yield OperateBtnGroup(
                app_ids=self.ids,
                labels=(
                    BtnLabel.chezmoi_add,
                    BtnLabel.chezmoi_apply,
                    BtnLabel.chezmoi_re_add,
                    BtnLabel.chezmoi_forget,
                    BtnLabel.chezmoi_destroy,
                ),
            )

    def on_mount(self) -> None:
        self.path_to_status = {}
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.contents_view = self.query_exactly_one(ContentsView)
        self.contents_view.display = False

    #################################
    # Watchers and message handling #
    #################################

    @on(SwitchGroupMsg)
    def handle_switch_group(self, msg: SwitchGroupMsg) -> None:
        switch_states: SwitchStates = msg.switch_states

        status_tree = self.query_exactly_one(StatusTree)
        managed_tree = self.query_exactly_one(ManagedTree)
        unmanaged_tree = self.query_exactly_one(UnManagedTree)
        unwanted_tree = self.query_exactly_one(UnWantedTree)

        # TODO: show hide relevant filters for a given displayed tree

        if switch_states.show_unwanted:
            tree_to_show = unwanted_tree
        elif switch_states.show_unmanaged:
            tree_to_show = unmanaged_tree
        elif switch_states.show_unchanged:
            tree_to_show = managed_tree
        else:
            tree_to_show = status_tree

        status_tree.display = status_tree is tree_to_show
        managed_tree.display = managed_tree is tree_to_show
        unmanaged_tree.display = unmanaged_tree is tree_to_show
        unwanted_tree.display = unwanted_tree is tree_to_show

    @on(RadioSet.Changed)
    def update_middle_view(self) -> None: ...

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[Path]) -> None:
        self.git_log_view.path = event.node.data
        self.contents_view.path = event.node.data

    @on(RadioSet.Changed)
    def toggle_view(self, event: RadioSet.Changed) -> None:
        if event.pressed.label == LabelStr.radio_git_log:
            self.git_log_view.display = True
            self.contents_view.display = False
        if event.pressed.label == LabelStr.radio_contents:
            self.git_log_view.display = False
            self.contents_view.display = True
