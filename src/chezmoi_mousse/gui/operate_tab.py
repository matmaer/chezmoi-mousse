from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, RadioButton, RadioSet, Static, TabPane, Tree

from chezmoi_mousse import path_funcs, store, tchezmoi
from chezmoi_mousse.gui.common.actionables import (
    OperateBtnGroup,
    SwitchGroup,
    TreeBtnGroup,
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
from chezmoi_mousse.str_enums import BtnLabel, LabelStr, ReadCmd, Tcss, TreeName

if TYPE_CHECKING:
    from pathlib import Path

    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import BtnDryData, NodeData
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["LeftSideVertical", "OperateTab", "RightSideVertical"]


class LeftSideVertical(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def compose(self) -> ComposeResult:
        yield TreeBtnGroup(classes=Tcss.tree_header)
        yield OperateTree(TreeName.managed_sp, store.op_ids.tree.managed_sp)
        yield OperateTree(TreeName.managed_amp, store.op_ids.tree.managed_amp)
        # UNMANAGED TREE VARIANTS
        yield OperateTree(
            TreeName.filtered_unman_sp, store.op_ids.tree.filtered_unman_sp
        )
        yield OperateTree(
            TreeName.filtered_unman_amp, store.op_ids.tree.filtered_unman_amp
        )
        # EXTENDED TREE
        yield OperateTree(TreeName.extended, store.op_ids.tree.extended)


class RightSideVertical(Vertical):
    def __init__(self, *, radio_labels: tuple[LabelStr, ...]) -> None:
        self.radio_labels = radio_labels
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(LabelStr.context, classes=Tcss.main_label)
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
        yield Static(LabelStr.context, classes=Tcss.main_label)
        yield Static(markup=False, classes=Tcss.blue_label)
        yield Static(markup=False, classes=Tcss.green_label)
        yield GitLogView()
        yield ContentView()
        yield DiffView()
        yield DiffReverseView()
        yield PathView()


class OperateTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

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
        yield OperateBtnGroup(labels=BtnLabel.op_btn_labels())

    def on_mount(self) -> None:
        self.dry_run_cache: dict[Path, dict[BtnLabel, BtnDryData]] = {}
        self.source_path_label = self.query_one(Tcss.green_label.q, Static)
        self.op_btn_group = self.query_exactly_one(OperateBtnGroup)
        self.op_buttons = self.op_btn_group.query_children(Button).results()

        self.left_side_vertical = self.query_exactly_one(LeftSideVertical)
        self.middle_vert = self.query_exactly_one(MiddleVertical)
        self.middle_label = self.middle_vert.query_one(Tcss.main_label.q, Static)
        self.no_show_label = self.middle_vert.query_one(Tcss.blue_label.q, Static)
        self.radio_set = self.query_exactly_one(RadioSet)

        self.paths_without_git_log: set[Path] = set()
        self.git_log_view = self.query_exactly_one(GitLogView)
        self.content_view = self.query_exactly_one(ContentView)
        self.diff_view = self.query_exactly_one(DiffView)
        self.diff_reverse_view = self.query_exactly_one(DiffReverseView)
        self.path_view = self.query_exactly_one(PathView)

    @property
    def current_displayed_tree(self) -> OperateTree:
        trees = self.left_side_vertical.query_children(OperateTree).results()
        for tree in trees:
            if tree and tree.display is True:
                return tree
        raise RuntimeError("Expected a tree to be displayed.")

    def show_dest_dir(self) -> None:
        if self.current_displayed_tree.root.data is None:
            return
        self._update_widgets(self.current_displayed_tree.root.data)
        self.current_displayed_tree.unselect()
        self.current_displayed_tree.scroll_home()

    def _update_widgets(self, node_data: NodeData) -> None:
        self.app.current_node = node_data
        size = self.middle_label.container_size.width
        self.middle_label.update(node_data.get_main_label(size))
        self._update_op_buttons(node_data)
        self._update_view_widgets(node_data)

    @work(description="update operate buttons enabled/disabled state")
    async def _update_op_buttons(self, node_data: NodeData) -> None:
        cached: dict[BtnLabel, BtnDryData] = {}
        try:
            cached = self.dry_run_cache[node_data.path]
        except:
            self.dry_run_cache[node_data.path] = await tchezmoi.get_dry_run_data(
                self.app, node_data.path
            )
            cached = self.dry_run_cache[node_data.path]
        for btn in self.op_btn_group.query(Button).results():
            btn_label = BtnLabel(str(btn.label))
            btn.disabled = cached[btn_label].no_op

    @work(description="update view widgets")
    async def _update_view_widgets(self, node_data: NodeData) -> None:
        if node_data.source_path is None:
            self.source_path_label.display = False
        else:
            rel_source_path = path_funcs.get_rel_path_str(node_data.source_path)
            self.source_path_label.update(f"source path: {rel_source_path}")
            self.source_path_label.display = True
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
                self.git_log_view.update_widgets(node_data, None)
                self.git_log_view.display = True
            elif node_data.path not in self.paths_without_git_log and (
                node_data.managed or node_data.dir_data.dest_dir
            ):
                cr = await tchezmoi.run_chezmoi_cmd(
                    self.app, ReadCmd.git_log, verb_arg=node_data.source_path
                )
                if cr.returncode != 0:
                    self.paths_without_git_log.add(node_data.path)
                else:
                    self.git_log_view.update_widgets(node_data, cr.std_out)
                    self.git_log_view.display = True
        elif radio_label == LabelStr.radio_contents and (
            node_data.file_path or node_data.path.is_file()
        ):
            self.content_view.node_data = node_data
            self.content_view.display = True
        elif radio_label == LabelStr.radio_diff and node_data.status_path:
            self.diff_view.node_data = node_data
            self.diff_view.display = True
        elif radio_label == LabelStr.radio_diff_reverse and node_data.status_path:
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

    @work(description="refresh trees")
    async def refresh_trees(self) -> bool:
        new_tree_paths = await tchezmoi.run_managed_commands(self.app)
        await store.store_new_tree_paths(self.app, new_tree_paths)
        if not store.cm_changes.changes_available:
            return False
        for tree in self.left_side_vertical.query_children(OperateTree).results():
            await tree.update_nodes(store.cm_changes)
        self.dry_run_cache.clear()
        self.content_view.cache.clear()
        self.diff_view.cache.clear()
        self.diff_reverse_view.cache.clear()
        self.git_log_view.cache.clear()
        self.paths_without_git_log.clear()
        tree_node = self.current_displayed_tree.node_map.get(self.app.current_node.path)
        if tree_node is None or tree_node.data is None:
            self.show_dest_dir()
        else:
            self._update_widgets(tree_node.data)
        return True

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeSelected)
    def set_path_for_views(self, event: Tree.NodeSelected[NodeData]) -> None:
        event.stop()
        if (
            event.node.data is None
            or event.control.id != self.current_displayed_tree.id
        ):
            return
        self._update_widgets(event.node.data)

    @on(Button.Pressed)
    def handle_dest_dir_btn(self, event: Button.Pressed) -> None:
        if (
            event.button.label == BtnLabel.dest_dir
            and self.app.current_node.path != store.cfg.dest_dir
        ):
            event.stop()
            self.show_dest_dir()

    @on(Button.Pressed)
    def handle_refresh_tree_btn(self, event: Button.Pressed) -> None:
        if event.button.label == BtnLabel.refresh:
            event.stop()
            refreshed = self.refresh_trees()
            if not refreshed:
                self.app.notify("No changes available, skipping refresh.")

    @on(Button.Pressed)
    def handle_expand_btn(self, event: Button.Pressed) -> None:
        if event.button.label == BtnLabel.expand:
            event.stop()
            self.current_displayed_tree.expand_top_level()

    @on(Button.Pressed)
    def handle_collapse_btn(self, event: Button.Pressed) -> None:
        if event.button.label == BtnLabel.collapse:
            event.stop()
            self.current_displayed_tree.collapse_bottom_level()

    @on(Button.Pressed)
    def handle_operate_button(self, event: Button.Pressed) -> None:
        if event.button.label not in BtnLabel.op_btn_labels():
            return
        event.stop()
        btn_label = BtnLabel(str(event.button.label))
        dry_run_data = self.dry_run_cache.get(self.app.current_node.path)
        if dry_run_data is None:
            self.app.notify("Affected paths are not available.", severity="warning")
            return
        paths = dry_run_data[btn_label]
        modal = OperateModal(
            op_btn=btn_label,
            node_data=self.app.current_node,
            paths_in_scope=paths.pretty_str,
        )
        self.app.push_screen(modal)

    @on(ShowTreeQidMsg)
    def handle_show_tree(self, msg: ShowTreeQidMsg) -> None:
        msg.stop()
        previous_tree = self.current_displayed_tree
        show_tree = self.query_one(msg.tree_id_q, OperateTree)
        previous_tree.display = False
        show_tree.display = True
        self._copy_expand_state(previous_tree, show_tree)
        self._select_current_node(show_tree)

    def _copy_expand_state(self, from_tree: OperateTree, to_tree: OperateTree) -> None:
        for path, from_node in from_tree.node_map.items():
            to_node = to_tree.node_map.get(path)
            if (
                to_node is None
                or to_node is to_tree.root
                or not to_node.allow_expand
                or to_node.is_expanded == from_node.is_expanded
            ):
                continue
            if from_node.is_expanded:
                to_node.expand()
            else:
                to_node.collapse()

    def _select_current_node(self, tree: OperateTree) -> None:
        node = tree.node_map.get(self.app.current_node.path)
        if node is None or node.data is None:
            return
        if node is tree.root:
            for tree in self.left_side_vertical.query_children(OperateTree).results():
                tree.unselect()
                tree.scroll_home() if tree.display else tree.scroll_home(animate=False)
            return
        parent = node.parent
        while parent is not None and parent is not tree.root:
            if not parent.is_expanded:
                parent.expand()
            parent = parent.parent

        def move_cursor() -> None:
            # After a refresh, so the node line numbers include the expanded parents.
            tree.move_cursor(node)
            tree.scroll_to_node(node)

        tree.call_after_refresh(move_cursor)
        self._update_view_widgets(node.data)

    @on(RadioSet.Changed)
    def switch_radio_view(self, event: RadioSet.Changed) -> None:
        event.stop()
        self._update_view_widgets(self.app.current_node)
