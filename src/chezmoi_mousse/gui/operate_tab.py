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
    Button,
    Label,
    RadioButton,
    RadioSet,
    Switch,
    TabPane,
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.actionables import OperateBtnGroup
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.labeled_views import (
    ContentView,
    DiffReverseView,
    DiffView,
    GitLogView,
    OperateViews,
)
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
from chezmoi_mousse.gui.common.messages import SwitchGroupMsg
from chezmoi_mousse.named_tuples import SwitchStates
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult


__all__ = ["OperateTab"]


class DestDirBtn(Button):
    def __init__(self) -> None:
        super().__init__(
            classes=Tcss.dest_dir_button,
        )

    def on_mount(self) -> None:
        self.label = f"{store.cfg.dest_dir}"


class LeftSideVertical(Vertical):
    def __init__(self) -> None:
        super().__init__(
            id=store.operate_ids.container.left_side, classes=Tcss.operations_left
        )

    def compose(self) -> ComposeResult:
        yield DestDirBtn()
        yield StatusTree()
        yield ManagedTree()
        yield UnManagedTree()
        yield UnWantedTree()
        yield ManagedTreeExpanded()
        yield StatusTreeExpanded()
        yield UnManagedTreeExpanded()
        yield UnWantedTreeExpanded()


class SwitchGroup(VerticalGroup):
    def __init__(self) -> None:
        self.ids = store.operate_ids
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
        radio_labels: tuple[LabelStr, ...],
    ) -> None:
        self.radio_labels = radio_labels
        super().__init__(
            id=store.operate_ids.container.right_side, classes=Tcss.operations_right
        )

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.context)
        with RadioSet():
            for radio_label in self.radio_labels:
                yield RadioButton(radio_label, compact=True)
        yield SwitchGroup()
        yield Button(
            label=BtnLabel.refresh_trees,
            classes=Tcss.refresh_button,
        )

    def on_mount(self) -> None:
        first_radio = self.query_one(RadioSet).query(RadioButton).first()
        if first_radio:
            first_radio.value = True


class OperateTab(TabPane):
    def __init__(self) -> None:
        super().__init__(
            id=BtnLabel.operate.pane_id,
            title=BtnLabel.operate,
        )

    def compose(self) -> ComposeResult:
        with Horizontal(classes=Tcss.operate_pane):
            yield LeftSideVertical()
            yield OperateViews()
            yield RightSideVertical(
                radio_labels=(
                    LabelStr.radio_git_log,
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                ),
            )
            yield OperateBtnGroup(
                store.operate_ids,
                labels=(
                    BtnLabel.chezmoi_add,
                    BtnLabel.chezmoi_apply,
                    BtnLabel.chezmoi_re_add,
                    BtnLabel.chezmoi_forget,
                    BtnLabel.chezmoi_destroy,
                ),
            )

    def on_mount(self) -> None:
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.contents_view = self.query_exactly_one(ContentView)

        self.man_tree = self.query_exactly_one(ManagedTree)
        self.man_tree_expanded = self.query_exactly_one(ManagedTreeExpanded)
        self.status_tree = self.query_exactly_one(StatusTree)
        self.status_tree_expanded = self.query_exactly_one(StatusTreeExpanded)
        self.unman_tree = self.query_exactly_one(UnManagedTree)
        self.unman_tree_expanded = self.query_exactly_one(UnManagedTreeExpanded)
        self.unwanted_tree = self.query_exactly_one(UnWantedTree)
        self.unwanted_tree_expanded = self.query_exactly_one(UnWantedTreeExpanded)

    #################################
    # Watchers and message handling #
    #################################

    @on(SwitchGroupMsg)
    def handle_switch_group(self, msg: SwitchGroupMsg) -> None:
        switch_states: SwitchStates = msg.switch_states

        if switch_states.expand_all:
            if switch_states.show_unwanted:
                tree_to_show = self.unwanted_tree_expanded
            elif switch_states.show_unmanaged:
                tree_to_show = self.unman_tree_expanded
            elif switch_states.show_unchanged:
                tree_to_show = self.man_tree_expanded
            else:
                tree_to_show = self.status_tree_expanded
        else:
            if switch_states.show_unwanted:
                tree_to_show = self.unwanted_tree
            elif switch_states.show_unmanaged:
                tree_to_show = self.unman_tree
            elif switch_states.show_unchanged:
                tree_to_show = self.man_tree
            else:
                tree_to_show = self.status_tree

        self.man_tree_expanded.display = self.man_tree_expanded is tree_to_show
        self.man_tree.display = self.man_tree is tree_to_show
        self.status_tree_expanded.display = self.status_tree_expanded is tree_to_show
        self.status_tree.display = self.status_tree is tree_to_show
        self.unman_tree_expanded.display = self.unman_tree_expanded is tree_to_show
        self.unman_tree.display = self.unman_tree is tree_to_show
        self.unwanted_tree_expanded.display = (
            self.unwanted_tree_expanded is tree_to_show
        )
        self.unwanted_tree.display = self.unwanted_tree is tree_to_show

    def set_view_path_reactives(self, path: Path) -> None:
        self.git_log_view.path = path
        self.diff_view.path = path
        self.diff_reverse_view.path = path
        self.contents_view.path = path
        return

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[Path]) -> None:
        assert event.node.data is not None
        self.set_view_path_reactives(event.node.data)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == str(store.cfg.dest_dir):
            event.stop()
            self.set_view_path_reactives(store.cfg.dest_dir)

    @on(RadioSet.Changed)
    def toggle_view(self, event: RadioSet.Changed) -> None:
        event.stop()
        if event.pressed.label == LabelStr.radio_git_log:
            self.git_log_view.display = True
            self.contents_view.display = False
            self.diff_view.display = False
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_contents:
            self.git_log_view.display = False
            self.contents_view.display = True
            self.diff_view.display = False
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_diff:
            self.git_log_view.display = False
            self.contents_view.display = False
            self.diff_view.display = True
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_diff_reverse:
            self.git_log_view.display = False
            self.contents_view.display = False
            self.diff_view.display = False
            self.diff_reverse_view.display = True
