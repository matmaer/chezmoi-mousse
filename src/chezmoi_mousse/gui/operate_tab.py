from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Horizontal,
    Vertical,
)
from textual.widgets import (
    Button,
    RadioButton,
    RadioSet,
    Switch,
    TabPane,
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.actionables import OperateBtnGroup, SwitchGroup
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.managed_trees import OperateTree
from chezmoi_mousse.gui.common.messages import SwitchGroupMsg
from chezmoi_mousse.gui.common.operate_views import (
    ContentView,
    DiffReverseView,
    DiffView,
    GitLogView,
)
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult

    from chezmoi_mousse.named_tuples import SwitchStates


__all__ = ["OperateTab"]


class LeftSideVertical(Vertical):
    def __init__(self) -> None:
        super().__init__(
            id=store.op_ids.container.left_side, classes=Tcss.operations_left
        )

    def compose(self) -> ComposeResult:
        yield Button(label=f"{store.cfg.dest_dir}", classes=Tcss.dest_dir_button)
        yield OperateTree(
            store.op_ids.tree.status,
            store.cm_paths.status_tree_dirs,
            store.cm_paths.status_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.status_xpd,
            store.cm_paths.status_tree_dirs,
            store.cm_paths.status_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.managed,
            store.cm_paths.man_tree_dirs,
            store.cm_paths.man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.managed_xpd,
            store.cm_paths.man_tree_dirs,
            store.cm_paths.man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_managed,
            store.cm_paths.un_man_tree_dirs,
            store.cm_paths.un_man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_managed_xpd,
            store.cm_paths.un_man_tree_dirs,
            store.cm_paths.un_man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_wanted,
            store.cm_paths.all_tree_dirs,
            store.cm_paths.all_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_wanted_xpd,
            store.cm_paths.all_tree_dirs,
            store.cm_paths.all_tree_files,
        )


class RightSideVertical(Vertical):
    def __init__(
        self,
        *,
        radio_labels: tuple[LabelStr, ...],
    ) -> None:
        self.radio_labels = radio_labels
        super().__init__(
            id=store.op_ids.container.right_side, classes=Tcss.operations_right
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
        first_radio = self.query_exactly_one(RadioSet).query(RadioButton).first()
        if first_radio:
            first_radio.value = True


class OperateTab(TabPane):
    def __init__(self) -> None:
        self.ids = store.op_ids
        super().__init__(
            id=BtnLabel.operate.pane_id,
            title=BtnLabel.operate,
        )

    def compose(self) -> ComposeResult:
        with Horizontal(classes=Tcss.operate_pane):
            yield LeftSideVertical()
            with Vertical(id=self.ids.container.middle, classes=Tcss.operations_middle):
                yield MainSectionLabel(LabelStr.dest_dir)
                yield GitLogView()
                yield ContentView()
                yield DiffView()
                yield DiffReverseView()
            yield RightSideVertical(
                radio_labels=(
                    LabelStr.radio_git_log,
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                ),
            )
            yield OperateBtnGroup(
                store.op_ids,
                labels=(
                    BtnLabel.chezmoi_add,
                    BtnLabel.chezmoi_apply,
                    BtnLabel.chezmoi_re_add,
                    BtnLabel.chezmoi_forget,
                    BtnLabel.chezmoi_destroy,
                ),
            )

    def on_mount(self) -> None:
        view_container = self.query_one(self.ids.container.middle_q)
        self.view_label = view_container.query_exactly_one(MainSectionLabel)
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.content_view = self.query_exactly_one(ContentView)
        self._set_all_path_reactives(store.cfg.dest_dir)

    #################################
    # Watchers and message handling #
    #################################

    @on(SwitchGroupMsg)
    def handle_switch_group(self, msg: SwitchGroupMsg) -> None:
        switch_states: SwitchStates = msg.switch_states
        tree_ids = store.op_ids.tree

        if switch_states.expand_all:
            if switch_states.show_unwanted:
                shown_id = tree_ids.un_wanted_xpd
            elif switch_states.show_unmanaged:
                shown_id = tree_ids.un_managed_xpd
            elif switch_states.show_unchanged:
                shown_id = tree_ids.managed_xpd
            else:
                shown_id = tree_ids.status_xpd
        else:
            if switch_states.show_unwanted:
                shown_id = tree_ids.un_wanted
            elif switch_states.show_unmanaged:
                shown_id = tree_ids.un_managed
            elif switch_states.show_unchanged:
                shown_id = tree_ids.managed
            else:
                shown_id = tree_ids.status

        for tree in self.query(OperateTree):
            tree.display = tree.id == shown_id

        # Show unwanted only makes sense for non-managed paths, as managed paths are
        # always wanted and disable 'expand_all' for trees including unwanted paths.
        switch_ids = store.op_ids.switch
        unwanted_switch = self.query_one(switch_ids.show_unwanted_q, Switch)
        expand_all_switch = self.query_one(switch_ids.expand_all_q, Switch)
        unwanted_switch.disabled = switch_states.expand_all or shown_id in (
            tree_ids.status,
            tree_ids.status_xpd,
            tree_ids.managed,
            tree_ids.managed_xpd,
        )
        expand_all_switch.disabled = shown_id in (
            tree_ids.un_wanted,
            tree_ids.un_wanted_xpd,
        )

    def _set_all_path_reactives(self, path: Path) -> None:
        self.git_log_view.path = path
        self.content_view.path = path
        self.diff_view.path = path
        self.diff_reverse_view.path = path

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[Path]) -> None:
        assert event.node.data is not None
        if event.node.data == store.cfg.dest_dir:
            self.view_label.update(LabelStr.dest_dir)
        else:
            self.view_label.update(store.cm_paths.path_labels[event.node.data])
        self._set_all_path_reactives(event.node.data)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == str(store.cfg.dest_dir):
            event.stop()
            self.view_label.update(LabelStr.dest_dir)
            self._set_all_path_reactives(store.cfg.dest_dir)

    @on(RadioSet.Changed)
    def toggle_view(self, event: RadioSet.Changed) -> None:
        event.stop()
        if event.pressed.label == LabelStr.radio_git_log:
            self.git_log_view.display = True
            self.content_view.display = False
            self.diff_view.display = False
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_contents:
            self.git_log_view.display = False
            self.content_view.display = True
            self.diff_view.display = False
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_diff:
            self.git_log_view.display = False
            self.content_view.display = False
            self.diff_view.display = True
            self.diff_reverse_view.display = False
        if event.pressed.label == LabelStr.radio_diff_reverse:
            self.git_log_view.display = False
            self.content_view.display = False
            self.diff_view.display = False
            self.diff_reverse_view.display = True
