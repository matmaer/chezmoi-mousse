from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.reactive import reactive
from textual.widgets import (
    Label,
    RadioButton,
    RadioSet,
    Switch,
    TabPane,
    Tree,
)

from chezmoi_mousse import store
from chezmoi_mousse.data_classes import ChezmoiPaths
from chezmoi_mousse.gui.common.actionables import (
    DestDirBtn,
    OperateBtn,
    RefreshBtn,
)
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.messages import DestDirBtnMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
    ColorVar,
    LabelStr,
    Tcss,
)

if TYPE_CHECKING:
    from textual import getters
    from textual.app import ComposeResult
    from textual.widgets.tree import TreeNode

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["OperateTab"]


class ManagedTree(Tree[Path]):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_unchanged: reactive[bool] = reactive(False, init=False)
    show_unmanaged: reactive[bool] = reactive(False, init=False)
    expand_all: reactive[bool] = reactive(False, init=False)

    def __init__(self) -> None:
        super().__init__(
            label="root",
            classes=Tcss.managed_tree,
        )

    def on_mount(self) -> None:
        self.path_to_node: dict[Path, TreeNode[Path]] = {}
        self.root.data = store.cfg.dest_dir
        self.path_to_node[store.cfg.dest_dir] = self.root
        self.guide_depth: int = 3
        self.show_root = False
        self.cm_paths = ChezmoiPaths.empty()

    def color_label(self, path: Path) -> str:
        italic = ""
        color_var = ColorVar.bogus
        if path in self.cm_paths.managed_dirs:
            status = self.cm_paths.managed_dirs[path]
            color_var = ColorVar.dimmed if status == "  " else ColorVar.text_primary
        elif path in self.cm_paths.managed_files:
            status = self.cm_paths.managed_files[path]
            color_var = ColorVar.dimmed if status == "  " else ColorVar.text_warning
        if path in self.cm_paths.sets.missing_paths:
            italic = " italic"
        color = self.app.theme_variables.get(color_var.value, ColorVar.bogus.value)
        markup_text = f"[{color}{italic}]{path.name}[/]"
        return markup_text

    async def update_tree(self, cm_paths: ChezmoiPaths) -> None:
        self.cm_paths = cm_paths
        for path in cm_paths.managed_dirs:
            if path.parent == store.cfg.dest_dir:
                label = self.color_label(path)
                self.root.add(label=label, data=path)
        for path in cm_paths.managed_files:
            if path.parent == store.cfg.dest_dir:
                label = self.color_label(path)
                self.root.add_leaf(label=label, data=path)

    #################################
    # Watchers and message handling #
    #################################

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, event: Tree.NodeCollapsed[Path]) -> None:
        if event.node is self.root:
            event.node.expand()

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, _: Tree.NodeExpanded[Path]) -> None: ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, event: Tree.NodeSelected[Path]) -> None:
        if event.node.data == store.cfg.dest_dir:
            return
        if event.node.data is None:
            return


class LeftSideVertical(Vertical):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, *, app_ids: AppIds) -> None:
        self.ids = app_ids
        super().__init__(id=app_ids.container.left_side, classes=Tcss.operations_left)

    def compose(self) -> ComposeResult:
        yield DestDirBtn(app_ids=self.ids)
        yield ManagedTree()
        yield RefreshBtn(app_ids=self.ids)

    @on(DestDirBtnMsg)
    def handle_dest_dir_btn_msg(self, msg: DestDirBtnMsg) -> None:
        self.notify(f"DestDirBtn pressed: {msg.tab_label}")


class MiddleVertical(Vertical):
    def __init__(self, *, app_ids: AppIds) -> None:
        self.ids = app_ids
        super().__init__(id=app_ids.container.middle, classes=Tcss.operations_middle)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.middle)


class RightSideVertical(Vertical):
    def __init__(
        self,
        *,
        app_ids: AppIds,
        op_btn_labels: tuple[BtnLabel, ...],
        radio_labels: tuple[LabelStr, ...],
        switch_labels: tuple[LabelStr, ...],
    ) -> None:
        self.ids = app_ids
        self.op_btn_labels = op_btn_labels
        self.radio_labels = radio_labels
        self.switch_labels = switch_labels
        super().__init__(id=app_ids.container.right_side, classes=Tcss.operations_right)

    def compose(self) -> ComposeResult:
        with VerticalGroup(classes=Tcss.op_btn_vert_group):
            for btn_label in self.op_btn_labels:
                yield OperateBtn(app_ids=self.ids, btn_label=btn_label)
        with RadioSet(id="focus_me"):
            for radio_label in self.radio_labels:
                yield RadioButton(radio_label, compact=True)

        with VerticalGroup(classes=Tcss.switches_vert_group):
            for switch_label in self.switch_labels:
                yield HorizontalGroup(
                    Switch(id=self.ids.switch_id(switch_label=switch_label)),
                    Label(switch_label),
                    classes=Tcss.switch_with_label,
                )

    def on_mount(self) -> None:
        first_radio = self.query_one(RadioSet).query(RadioButton).first()
        if first_radio:
            first_radio.value = True


class OperateTab(TabPane):
    def __init__(self) -> None:
        self.ids = store.man_tree_ids
        super().__init__(
            id=BtnLabel.operate.pane_id,
            title=BtnLabel.operate,
        )

    def compose(self) -> ComposeResult:
        with Horizontal(classes=Tcss.operate_pane):
            yield LeftSideVertical(app_ids=self.ids)
            yield MiddleVertical(app_ids=self.ids)
            yield RightSideVertical(
                app_ids=self.ids,
                op_btn_labels=(
                    BtnLabel.chezmoi_add,
                    BtnLabel.chezmoi_apply,
                    BtnLabel.chezmoi_re_add,
                    BtnLabel.chezmoi_forget,
                    BtnLabel.chezmoi_destroy,
                ),
                radio_labels=(
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                    LabelStr.radio_git_log,
                ),
                switch_labels=(
                    LabelStr.show_unchanged,
                    LabelStr.expand_all,
                    LabelStr.show_unmanaged,
                    LabelStr.show_unwanted,
                ),
            )

    def on_mount(self) -> None:
        self.path_to_status = {}  # Initialize the path_to_status dictionary

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        managed_tree = self.query_one(self.ids.managed_tree_q, ManagedTree)
        if event.switch.id == self.ids.switch.show_unchanged:
            managed_tree.show_unchanged = event.value
        elif event.switch.id == self.ids.switch.show_unmanaged:
            managed_tree.show_unmanaged = event.value
        elif event.switch.id == self.ids.switch.expand_all:
            managed_tree.expand_all = event.value
