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
from chezmoi_mousse.gui.common.messages import DestDirBtnMsg, SwitchGroupMsg
from chezmoi_mousse.str_enums import (
    BtnLabel,
    LabelStr,
    Tcss,
)

if TYPE_CHECKING:
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["OperateTab"]


type SwitchState = dict[str, bool]


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
        yield ChezmoiTree()

    @on(DestDirBtnMsg)
    def handle_dest_dir_btn_msg(self, msg: DestDirBtnMsg) -> None:
        self.notify(f"DestDirBtn pressed: {msg.tab_label}")


class MiddleVertical(Vertical):
    def __init__(self, *, ids: AppIds) -> None:
        self.ids = ids
        super().__init__(id=ids.container.middle, classes=Tcss.operations_middle)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel(LabelStr.middle)


class SwitchGroup(VerticalGroup):
    def compose(self) -> ComposeResult:
        switch_labels = (
            LabelStr.show_unchanged,
            LabelStr.expand_all,
            LabelStr.show_unmanaged,
            LabelStr.show_unwanted,
        )
        for switch_label in switch_labels:
            yield HorizontalGroup(
                Switch(name=switch_label.name),
                Label(switch_label),
                classes=Tcss.switch_with_label,
            )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        switches = self.query(Switch)
        switch_states: SwitchState = {
            switch.name: switch.value for switch in switches if switch.name
        }
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
        yield SwitchGroup(classes=Tcss.switches_vert_group)
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
            yield MiddleVertical(ids=self.ids)
            yield RightSideVertical(
                ids=self.ids,
                radio_labels=(
                    LabelStr.radio_contents,
                    LabelStr.radio_diff,
                    LabelStr.radio_diff_reverse,
                    LabelStr.radio_git_log,
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

    @on(SwitchGroupMsg)
    def handle_switch_group(self, message: SwitchGroupMsg) -> None:
        switch_states = message.switch_states
        # Handle the switch states as needed
        self.notify(f"{switch_states}")
