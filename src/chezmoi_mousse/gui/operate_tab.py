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
    TabPane,
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.actionables import OperateBtnGroup, SwitchGroup
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.managed_trees import OperateTree
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
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
            store.op_ids.tree.un_managed_su,
            store.cm_paths.un_man_tree_dirs,
            store.cm_paths.un_man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_managed_xpd,
            store.cm_paths.un_man_tree_dirs,
            store.cm_paths.un_man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_managed_xpd_su,
            store.cm_paths.un_man_tree_dirs,
            store.cm_paths.un_man_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_wanted,
            store.cm_paths.all_tree_dirs,
            store.cm_paths.all_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_wanted_su,
            store.cm_paths.all_tree_dirs,
            store.cm_paths.all_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_wanted_xpd,
            store.cm_paths.all_tree_dirs,
            store.cm_paths.all_tree_files,
        )
        yield OperateTree(
            store.op_ids.tree.un_wanted_xpd_su,
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
        self.status_tree = self.query_one(self.ids.tree.status_q, OperateTree)
        self.status_tree_xpd = self.query_one(self.ids.tree.status_xpd_q, OperateTree)
        self.managed_tree = self.query_one(self.ids.tree.managed_q, OperateTree)
        self.managed_tree_xpd = self.query_one(self.ids.tree.managed_xpd_q, OperateTree)
        self.unmanaged_tree = self.query_one(self.ids.tree.un_managed_q, OperateTree)
        self.unmanaged_tree_xpd = self.query_one(
            self.ids.tree.un_managed_xpd_q, OperateTree
        )
        self.unwanted_tree = self.query_one(self.ids.tree.un_wanted_q, OperateTree)
        self.unwanted_tree_xpd = self.query_one(
            self.ids.tree.un_wanted_xpd_q, OperateTree
        )
        self.show_unchanged_switch = self.query_one(self.ids.switch.show_unchanged_q)
        self.show_unmanaged_switch = self.query_one(self.ids.switch.show_unmanaged_q)
        self.show_unwanted_switch = self.query_one(self.ids.switch.show_unwanted_q)
        self.view_label = view_container.query_exactly_one(MainSectionLabel)
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.content_view = self.query_exactly_one(ContentView)

    @property
    def current_tree(self) -> OperateTree:
        for tree in self.query(OperateTree).results():
            if tree.display:
                return tree
        raise RuntimeError("No tree is displayed")

    def set_tree_display(self, show_tree: OperateTree) -> None:
        for tree in self.query(OperateTree).results():
            if tree == show_tree:
                tree.display = True
            else:
                tree.display = False

    #################################
    # Watchers and message handling #
    #################################

    @on(ShowTreeQidMsg)
    def handle_show_tree(self, msg: ShowTreeQidMsg) -> None:
        tree_qid: str = msg.tree_qid
        self.notify(f"received {tree_qid}")

        # hide the current tree:
        all_trees = self.query(OperateTree).results()
        for tree in all_trees:
            tree.display = False
        show_tree = self.query_exactly_one(tree_qid, OperateTree)
        show_tree.display = True

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
