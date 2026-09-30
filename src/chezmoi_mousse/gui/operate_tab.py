from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Horizontal,
    Vertical,
)
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    RadioButton,
    RadioSet,
    Static,
    TabPane,
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.data_types import NodeData
from chezmoi_mousse.gui.common.actionables import (
    OperateBtnGroup,
    PromptBtnGroup,
    SwitchGroup,
)
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.common.operate_views import (
    ContentView,
    DiffReverseView,
    DiffView,
    GitLogView,
)
from chezmoi_mousse.str_enums import (
    BtnLabel,
    ChezmoiPrompts,
    LabelStr,
    ReactiveVar,
    StatusCode as Sc,
    Tcss,
    TreeName,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["OperateTab"]


class ChezmoiCmdModal(ModalScreen[None]):
    def __init__(self, btn_label: str) -> None:
        self.btn_label = btn_label
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"{self.btn_label}: Not yet implemented")
            yield PromptBtnGroup(
                labels=(
                    ChezmoiPrompts.all.btn_label,
                    ChezmoiPrompts.diff.btn_label,
                    ChezmoiPrompts.edit.btn_label,
                    ChezmoiPrompts.no.btn_label,
                    ChezmoiPrompts.no_to_all.btn_label,
                    ChezmoiPrompts.quit.btn_label,
                    ChezmoiPrompts.yes.btn_label,
                    BtnLabel.close,
                ),
            )

    @on(Button.Pressed)
    def cancel(self) -> None:
        self.dismiss()


class LeftSideVertical(Vertical):
    switch_state: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__(
            id=store.op_ids.container.left_side, classes=Tcss.operations_left
        )

    def compose(self) -> ComposeResult:
        yield Button(label=f"{store.cfg.dest_dir}", classes=Tcss.dest_dir_button)
        yield OperateTree(
            TreeName.managed_only_sp,
            store.op_ids.tree.managed_only_sp,
        )
        yield OperateTree(
            TreeName.managed_only_sp_xpd,
            store.op_ids.tree.managed_only_sp_xpd,
        )
        yield OperateTree(
            TreeName.managed_all_mp,
            store.op_ids.tree.managed_all_mp,
        )
        yield OperateTree(
            TreeName.managed_all_mp_xpd,
            store.op_ids.tree.managed_all_mp_xpd,
        )
        # UNMANAGED TREE VARIANTS
        yield OperateTree(
            TreeName.un_man_plus_sp,
            store.op_ids.tree.un_man_plus_sp,
        )
        yield OperateTree(
            TreeName.un_man_plus_sp_xpd,
            store.op_ids.tree.un_man_plus_sp_xpd,
        )
        yield OperateTree(
            TreeName.un_man_plus_amp,
            store.op_ids.tree.un_man_plus_amp,
        )
        yield OperateTree(
            TreeName.un_man_plus_amp_xpd,
            store.op_ids.tree.un_man_plus_amp_xpd,
        )
        # UNWANTED TREE VARIANTS
        yield OperateTree(
            TreeName.un_wanted_plus_sp,
            store.op_ids.tree.un_wanted_plus_sp,
        )
        yield OperateTree(
            TreeName.un_wanted_plus_sp_xpd,
            store.op_ids.tree.un_wanted_plus_sp_xpd,
        )
        yield OperateTree(
            TreeName.un_wanted_plus_amp,
            store.op_ids.tree.un_wanted_plus_amp,
        )
        yield OperateTree(
            TreeName.un_wanted_plus_amp_xpd,
            store.op_ids.tree.un_wanted_plus_amp_xpd,
        )

    @property
    def _current_displayed_tree_id(self) -> str | None:
        for tree in self.query_children(OperateTree).results():
            if tree.display is True:
                return tree.id
        return None

    @property
    def _non_displayed_trees(self) -> list[OperateTree]:
        return [
            tree
            for tree in self.query_children(OperateTree).results()
            if tree.display is False
        ]

    def _sync_to_trees(self, node_data: NodeData, exclude: list[OperateTree]) -> None:
        for tree in self._non_displayed_trees:
            if tree in exclude:
                continue
            tree_node = tree.node_map.get(node_data.path)
            if tree_node:
                tree.select_node(tree_node)

    @on(Tree.NodeSelected)
    def sync_selected_node(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            return
        if (
            self._current_displayed_tree_id is None
            or event.control.id != self._current_displayed_tree_id
            or (
                event.control.id
                in (
                    store.op_ids.tree.un_wanted_plus_sp,
                    store.op_ids.tree.un_wanted_plus_amp,
                )
                and event.node.data.status == Sc.XX
            )
        ):
            return
        exclude: list[OperateTree] = []
        if event.node.data.status in (Sc.SS, Sc.UU, Sc.XX):
            exclude.extend(
                [
                    self.query_one(store.op_ids.tree.managed_only_sp_q, OperateTree),
                    self.query_one(
                        store.op_ids.tree.managed_only_sp_xpd_q, OperateTree
                    ),
                ]
            )
        if event.node.data.status in (Sc.UU, Sc.XX):
            exclude.extend(
                [
                    self.query_one(store.op_ids.tree.managed_all_mp_q, OperateTree),
                    self.query_one(store.op_ids.tree.managed_all_mp_xpd_q, OperateTree),
                ]
            )
        if event.node.data.status in (Sc.XX):
            exclude.extend(
                [
                    self.query_one(store.op_ids.tree.un_man_plus_sp_q, OperateTree),
                    self.query_one(store.op_ids.tree.un_man_plus_amp_q, OperateTree),
                    self.query_one(store.op_ids.tree.un_man_plus_sp_xpd_q, OperateTree),
                    self.query_one(
                        store.op_ids.tree.un_man_plus_amp_xpd_q, OperateTree
                    ),
                ]
            )
        self._sync_to_trees(event.node.data, exclude=exclude)

    @on(Tree.NodeCollapsed)
    def sync_collapsed_node(self, event: Tree.NodeCollapsed[NodeData]) -> None: ...

    @on(Tree.NodeExpanded)
    def sync_expanded_node(self, event: Tree.NodeExpanded[NodeData]) -> None: ...


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
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        self.ids = store.op_ids
        self.root_node_data: NodeData = NodeData(
            path=store.cfg.dest_dir,
            status=Sc.QQ,
            main_label=LabelStr.dest_dir,
            exists=True,
        )
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
        view_container = self.query_one(self.ids.container.middle_q, Vertical)
        self.view_label = view_container.query_exactly_one(MainSectionLabel)
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.content_view = self.query_exactly_one(ContentView)
        self.op_btn_group = self.query_exactly_one(OperateBtnGroup)
        for btn in self.op_btn_group.query(Button).results():
            if btn.label == BtnLabel.chezmoi_destroy:
                btn.disabled = True
            if btn.label == BtnLabel.chezmoi_forget:
                btn.disabled = True

    #################################
    # Watchers and message handling #
    #################################

    @on(ShowTreeQidMsg)
    def handle_show_tree(self, msg: ShowTreeQidMsg) -> None:

        # hide the current tree:
        all_trees = self.query(OperateTree).results()
        for tree in all_trees:
            tree.display = False
        show_tree = self.query_one(msg.tree_id_q, OperateTree)
        show_tree.display = True

    def _disable_enable_op_buttons(self, path: Path) -> None:
        for btn in self.op_btn_group.query(Button).results():
            if btn.label == BtnLabel.chezmoi_add:
                btn.disabled = path not in store.cm_paths.add_btn_paths
            if btn.label == BtnLabel.chezmoi_apply:
                btn.disabled = path not in store.cm_paths.apply_btn_paths
            if btn.label == BtnLabel.chezmoi_destroy:
                btn.disabled = path not in store.cm_paths.destroy_btn_paths
            if btn.label == BtnLabel.chezmoi_forget:
                btn.disabled = path not in store.cm_paths.forget_btn_paths
            if btn.label == BtnLabel.chezmoi_re_add:
                btn.disabled = path not in store.cm_paths.re_add_btn_paths

    def _set_all_path_reactives(self, node_data: NodeData) -> None:
        setattr(self.git_log_view, ReactiveVar.node_data, node_data)
        setattr(self.content_view, ReactiveVar.node_data, node_data)
        setattr(self.diff_view, ReactiveVar.node_data, node_data)
        setattr(self.diff_reverse_view, ReactiveVar.node_data, node_data)

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[NodeData]) -> None:
        if event.node.data is None:
            return
        event.stop()
        self.view_label.update(event.node.data.main_label)
        self._set_all_path_reactives(event.node.data)
        self._disable_enable_op_buttons(event.node.data.path)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == str(store.cfg.dest_dir):
            event.stop()
            self.view_label.update(LabelStr.dest_dir)
            self._set_all_path_reactives(self.root_node_data)
            for btn in self.op_btn_group.query(Button).results():
                if btn.label == BtnLabel.chezmoi_destroy:
                    btn.disabled = True
                if btn.label == BtnLabel.chezmoi_forget:
                    btn.disabled = True

    @on(Button.Pressed)
    def handle_operate_button(self, event: Button.Pressed) -> None:
        if event.button.label in (
            BtnLabel.chezmoi_add,
            BtnLabel.chezmoi_apply,
            BtnLabel.chezmoi_re_add,
            BtnLabel.chezmoi_forget,
            BtnLabel.chezmoi_destroy,
        ):
            event.stop()
        self.app.push_screen(ChezmoiCmdModal(str(event.button.label)))

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
