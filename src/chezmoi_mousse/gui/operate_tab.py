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
from chezmoi_mousse.gui.common.components import MainSectionLabel
from chezmoi_mousse.gui.common.managed_trees import (
    ChezmoiTree,
    ManagedTree,
    StatusTree,
)
from chezmoi_mousse.gui.common.messages import DestDirBtnMsg
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

    def __init__(self, *, app_ids: AppIds) -> None:
        self.ids = app_ids
        super().__init__(id=app_ids.container.left_side, classes=Tcss.operations_left)

    def compose(self) -> ComposeResult:
        yield DestDirBtn(app_ids=self.ids)
        yield ManagedTree()
        yield StatusTree()
        yield ChezmoiTree()

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
        radio_labels: tuple[LabelStr, ...],
        switch_labels: tuple[LabelStr, ...],
    ) -> None:
        self.ids = app_ids
        self.radio_labels = radio_labels
        self.switch_labels = switch_labels
        super().__init__(id=app_ids.container.right_side, classes=Tcss.operations_right)

    def compose(self) -> ComposeResult:
        with RadioSet():
            for radio_label in self.radio_labels:
                yield RadioButton(radio_label, compact=True)

        with VerticalGroup(classes=Tcss.switches_vert_group):
            for switch_label in self.switch_labels:
                yield HorizontalGroup(
                    Switch(id=self.ids.switch_id(switch_label=switch_label)),
                    Label(switch_label),
                    classes=Tcss.switch_with_label,
                )

        yield RefreshBtn(app_ids=self.ids)

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
        self.path_to_status = {}  # Initialize the path_to_status dictionary

    #################################
    # Watchers and message handling #
    #################################

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        full_man_tree = self.query_exactly_one(ManagedTree)
        status_man_tree = self.query_exactly_one(StatusTree)
        if event.switch.id == self.ids.switch.show_unchanged:
            full_man_tree.display = not full_man_tree.display
            status_man_tree.display = not status_man_tree.display
        elif event.switch.id == self.ids.switch.show_unmanaged:
            self.notify(f"Show unmanaged: {event.value}")
        elif event.switch.id == self.ids.switch.expand_all:
            self.notify(f"Expand all: {event.value}")

    # To implement

    @on(Tree.NodeCollapsed)
    def handle_node_collapsed(self, _: Tree.NodeCollapsed[Path]) -> None: ...

    @on(Tree.NodeExpanded)
    def handle_node_expanded(self, _: Tree.NodeExpanded[Path]) -> None: ...

    @on(Tree.NodeSelected)
    def send_node_context_message(self, _: Tree.NodeSelected[Path]) -> None: ...
