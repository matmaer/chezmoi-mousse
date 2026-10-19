from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, RadioButton, RadioSet, TabPane, Tree

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.gui.common.actionables import OperateBtnGroup, SwitchGroup
from chezmoi_mousse.gui.common.components import (
    MainSectionLabel,
    NoShowLabel,
    SubSectionLabel,
)
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
from chezmoi_mousse.gui.common.operate_modal import OperateModal
from chezmoi_mousse.gui.common.operate_tree import OperateTree
from chezmoi_mousse.gui.common.operate_views import (
    ContentView,
    DiffReverseView,
    DiffView,
    GitLogView,
    PathView,
)
from chezmoi_mousse.str_enums import BtnLabel, Chars, LabelStr, ReadCmd, Tcss, TreeName
from chezmoi_mousse.tchezmoi import OperatePaths

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["LeftSideVertical", "OperateTab", "RightSideVertical"]


class LeftSideVertical(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button(label=f"{store.cfg.dest_dir}", classes=Tcss.dest_dir_button),
            Button(label=Chars.refresh, classes=Tcss.refresh_button),
            classes=Tcss.tree_header,
        )
        yield OperateTree(TreeName.managed_sp, store.op_ids.tree.managed_sp)
        yield OperateTree(TreeName.managed_sp_xpd, store.op_ids.tree.managed_sp_xpd)
        yield OperateTree(TreeName.managed_amp, store.op_ids.tree.managed_amp)
        yield OperateTree(TreeName.managed_amp_xpd, store.op_ids.tree.managed_amp_xpd)
        # UNMANAGED TREE VARIANTS
        yield OperateTree(TreeName.wanted_plus_sp, store.op_ids.tree.wanted_plus_sp)
        yield OperateTree(
            TreeName.wanted_plus_sp_xpd, store.op_ids.tree.wanted_plus_sp_xpd
        )
        yield OperateTree(TreeName.wanted_plus_amp, store.op_ids.tree.wanted_plus_amp)
        yield OperateTree(
            TreeName.wanted_plus_amp_xpd, store.op_ids.tree.wanted_plus_amp_xpd
        )
        # UNWANTED TREE VARIANTS
        yield OperateTree(
            TreeName.un_wanted_plus_sp, store.op_ids.tree.un_wanted_plus_sp
        )
        yield OperateTree(
            TreeName.un_wanted_plus_sp_xpd, store.op_ids.tree.un_wanted_plus_sp_xpd
        )
        yield OperateTree(
            TreeName.un_wanted_plus_amp, store.op_ids.tree.un_wanted_plus_amp
        )
        yield OperateTree(
            TreeName.un_wanted_plus_amp_xpd, store.op_ids.tree.un_wanted_plus_amp_xpd
        )

    @on(Button.Pressed)
    def handle_refresh_tree_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label == Chars.refresh:
            event.stop()
            self._refresh_trees()

    @work
    async def _refresh_trees(self) -> None:
        await tchezmoi.run_managed_commands(self.app)

    async def apply_changes(self) -> None:
        if store.cm_changes.changes_available:
            for tree in self.query_children(OperateTree).results():
                await tree.apply_changes(store.cm_changes)


class RightSideVertical(Vertical):
    def __init__(self, *, radio_labels: tuple[LabelStr, ...]) -> None:
        self.radio_labels = radio_labels
        super().__init__()

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.context)
        with RadioSet():
            for radio_label in self.radio_labels:
                yield RadioButton(radio_label, compact=True)
        yield SwitchGroup()

    def on_mount(self) -> None:
        radio_set = self.query_exactly_one(RadioSet)
        first_radio = radio_set.query(RadioButton).first()
        with radio_set.prevent(RadioSet.Changed):
            if first_radio:
                first_radio.value = True


class MiddleVertical(Vertical):
    def compose(self) -> ComposeResult:
        yield MainSectionLabel()
        yield NoShowLabel()
        yield SubSectionLabel()
        yield GitLogView()
        yield ContentView()
        yield DiffView()
        yield DiffReverseView()
        yield PathView()


class OperateTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        self.ids = store.op_ids
        super().__init__(id=BtnLabel.operate.pane_id, title=BtnLabel.operate)

    def compose(self) -> ComposeResult:
        with Horizontal(classes=Tcss.operate_pane):
            yield LeftSideVertical()
            yield MiddleVertical()
            yield RightSideVertical(
                radio_labels=(
                    LabelStr.radio_git_log,
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                    LabelStr.radio_path_view,
                )
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
        self.operate_paths = OperatePaths()
        self.source_path_label = self.query_exactly_one(SubSectionLabel)
        self.no_show_label = self.query_exactly_one(NoShowLabel)

        self.left_side_vertical = self.query_exactly_one(LeftSideVertical)
        self.middle_vertical = self.query_exactly_one(MiddleVertical)
        self.op_btn_group = self.query_exactly_one(OperateBtnGroup)
        self.radio_set = self.query_exactly_one(RadioSet)

        self.paths_without_git_log: set[Path] = set()
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.content_view = self.query_exactly_one(ContentView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.path_view = self.query_exactly_one(PathView)

        self._update_all_widgets(store.cm_paths.dest_dir_node_data)

    @property
    def _current_displayed_tree(self) -> OperateTree:
        trees = self.left_side_vertical.query_children(OperateTree).results()
        for tree in trees:
            if tree and tree.display is True:
                return tree
        raise RuntimeError("Expected a tree to be displayed.")

    def _sync_non_displayed_trees(self, node_data: NodeData) -> None:
        # update other trees in the background
        trees = self.left_side_vertical.query_children(OperateTree).results()
        for tree in trees:
            if tree.display:
                continue
            tree_node = tree.node_map.get(node_data.path)
            if tree_node:
                with tree.prevent(
                    Tree.NodeSelected,
                    Tree.NodeExpanded,
                    Tree.NodeHighlighted,
                    Tree.NodeCollapsed,
                ):
                    tree.select_node(tree_node)
                tree.scroll_to_node(tree_node, animate=False)
            else:
                tree.unselect()

    def _update_all_widgets(self, node_data: NodeData) -> None:
        self.current_node: NodeData = node_data

        middle_label = self.middle_vertical.query_exactly_one(MainSectionLabel)
        size = middle_label.container_size.width
        middle_label.update(node_data.get_main_label(size))

        if node_data.source_path is None:
            self.source_path_label.display = False
        else:
            rel_source_path = path_funcs.get_rel_path_str(node_data.source_path)
            self.source_path_label.update(f"source path: {rel_source_path}")
            self.source_path_label.display = True

        self._update_op_buttons(node_data)
        self._sync_non_displayed_trees(node_data)
        self._update_view_widgets(node_data)

    @work
    async def _update_op_buttons(self, node_data: NodeData) -> None:
        for btn in self.op_btn_group.query(Button).results():
            btn.disabled = await self.operate_paths.disable_button(
                self.app, str(btn.label), node_data
            )

    @work
    async def _update_view_widgets(self, node_data: NodeData) -> None:
        self.no_show_label.display = False
        for view in (
            self.git_log_view,
            self.content_view,
            self.diff_view,
            self.diff_reverse_view,
            self.path_view,
        ):
            view.display = False
        assert self.radio_set.pressed_button is not None
        radio_label = str(self.radio_set.pressed_button.label)
        if radio_label == LabelStr.radio_git_log:
            if node_data.path in self.git_log_view.cache:
                self.git_log_view.update_git_log_view(node_data, None)
                self.git_log_view.display = True
            elif node_data.path not in self.paths_without_git_log and (
                node_data.managed or node_data.dest_dir
            ):
                cr = await tchezmoi.run_chezmoi_cmd(
                    self.app, ReadCmd.git_log, verb_arg=node_data.source_path
                )
                if cr.returncode != 0:
                    self.paths_without_git_log.add(node_data.path)
                else:
                    self.git_log_view.update_git_log_view(node_data, cr.std_out)
                    self.git_log_view.display = True
        elif radio_label == LabelStr.radio_contents and (
            node_data.file_path or node_data.path.is_file()
        ):
            self.content_view.node_data = node_data
            self.content_view.display = True
        elif radio_label == LabelStr.radio_diff and node_data.has_status:
            self.diff_view.node_data = node_data
            self.diff_view.display = True
        elif radio_label == LabelStr.radio_diff_reverse and node_data.has_status:
            self.diff_reverse_view.node_data = node_data
            self.diff_reverse_view.display = True
        elif radio_label == LabelStr.radio_path_view:
            self.path_view.node_data = node_data
            self.path_view.display = True
        if (
            not (
                self.git_log_view.display
                or self.content_view.display
                or self.diff_view.display
                or self.diff_reverse_view.display
            )
            and radio_label != LabelStr.radio_path_view
        ):
            map: dict[str, LabelStr] = {
                LabelStr.radio_git_log: LabelStr.select_git_log_path,
                LabelStr.radio_contents: LabelStr.select_file_path,
                LabelStr.radio_diff: LabelStr.select_status_path,
                LabelStr.radio_diff_reverse: LabelStr.select_status_path,
            }
            self.no_show_label.update(map[radio_label])
            self.no_show_label.display = True
            self.path_view.node_data = node_data
            self.path_view.display = True

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[NodeData]) -> None:
        event.stop()
        if (
            event.node.data is None
            or event.control.id != self._current_displayed_tree.id
            or event.node.data.path == self.current_node.path
        ):
            return
        self._update_all_widgets(event.node.data)

    @on(Button.Pressed)
    def handle_dest_dir_btn_msg(self, event: Button.Pressed) -> None:
        if event.button.label != str(store.cfg.dest_dir):
            return
        event.stop()
        self._update_all_widgets(store.cm_paths.dest_dir_node_data)
        for tree in self.left_side_vertical.query_children(OperateTree).results():
            tree.unselect()
            tree.scroll_home() if tree.display else tree.scroll_home(animate=False)

    @on(Button.Pressed)
    def handle_operate_button(self, event: Button.Pressed) -> None:
        if event.button.label not in (
            BtnLabel.chezmoi_add,
            BtnLabel.chezmoi_apply,
            BtnLabel.chezmoi_re_add,
            BtnLabel.chezmoi_forget,
            BtnLabel.chezmoi_destroy,
        ):
            return
        event.stop()
        modal = OperateModal(
            BtnLabel(str(event.button.label)),
            self.current_node.path,
            self.operate_paths.affected_paths(
                self.current_node.path, str(event.button.label)
            ),
        )
        self.app.push_screen(modal)

    @on(ShowTreeQidMsg)
    def handle_show_tree(self, msg: ShowTreeQidMsg) -> None:
        msg.stop()
        self._current_displayed_tree.display = False
        show_tree = self.query_one(msg.tree_id_q, OperateTree)
        show_tree.display = True

    @on(RadioSet.Changed)
    def switch_radio_view(self, event: RadioSet.Changed) -> None:
        event.stop()
        self._update_view_widgets(self.current_node)
