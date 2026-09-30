from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import on
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.widgets import Button, Label, Switch

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
from chezmoi_mousse.str_enums import LabelStr, Tcss

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.str_enums import BtnLabel


__all__ = [
    "FlatButtonsVertical",
    "OperateBtnGroup",
    "PromptBtnGroup",
    "SwitchGroup",
    "TabButtons",
]


class FlatButtonsVertical(Container):
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels: tuple[BtnLabel, ...] = labels
        super().__init__(id=app_ids.container.flat_buttons)

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield Button(
                id=self.app_ids.btn_id(btn_label=label),
                label=label,
                classes=Tcss.flat_button,
                flat=True,
            )

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query_children(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class OperateBtnGroup(HorizontalGroup):
    def __init__(self, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels = labels
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield Button(
                id=self.app_ids.btn_id(btn_label=btn_label),
                label=btn_label,
                classes=Tcss.operate_button,
            )


class PromptBtnGroup(HorizontalGroup):
    def __init__(self, labels: tuple[str, ...]) -> None:
        self.labels = labels
        super().__init__(
            id=store.op_ids.container.prompt_buttons, classes=Tcss.prompt_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield Button(label=btn_label, classes=Tcss.prompt_button)


class SwitchGroup(VerticalGroup):
    state_to_tree_map: ClassVar[dict[tuple[bool, ...], str]] = {
        # Managed trees including only paths with a status or meta status
        (False, False, False, False): store.op_ids.tree.managed_only_sp_q,
        (True, False, False, False): store.op_ids.tree.managed_only_sp_xpd_q,
        # Managed trees including all managed maths
        (False, True, False, False): store.op_ids.tree.managed_all_mp_q,
        (True, True, False, False): store.op_ids.tree.managed_all_mp_xpd_q,
        # Un-managed trees (show_unchanged is False)
        (False, False, True, False): store.op_ids.tree.un_man_plus_sp_q,
        (True, False, True, False): store.op_ids.tree.un_man_plus_sp_xpd_q,
        # Un-managed trees (show_unchanged is True)
        (False, True, True, False): store.op_ids.tree.un_man_plus_amp_q,
        (True, True, True, False): store.op_ids.tree.un_man_plus_amp_xpd_q,
        # Unwanted trees when show_unchanged is False (show_unmanaged switch disabled)
        (False, False, True, True): store.op_ids.tree.un_wanted_plus_sp_q,
        (True, False, True, True): store.op_ids.tree.un_wanted_plus_sp_xpd_q,
        (False, False, False, True): store.op_ids.tree.un_wanted_plus_sp_q,
        (True, False, False, True): store.op_ids.tree.un_wanted_plus_sp_xpd_q,
        # Unwanted trees when show_unchanged is True (show_unmanaged switch disabled)
        (False, True, False, True): store.op_ids.tree.un_wanted_plus_amp_q,
        (True, True, False, True): store.op_ids.tree.un_wanted_plus_amp_xpd_q,
        (False, True, True, True): store.op_ids.tree.un_wanted_plus_amp_q,
        (True, True, True, True): store.op_ids.tree.un_wanted_plus_amp_xpd_q,
    }

    def __init__(self) -> None:
        self.ids = store.op_ids
        super().__init__(classes=Tcss.switches_vert_group)

    def compose(self) -> ComposeResult:
        for switch_label in (
            LabelStr.expand_managed,
            LabelStr.show_unchanged,
            LabelStr.show_unmanaged,
            LabelStr.show_unwanted,
        ):
            yield HorizontalGroup(
                Switch(id=self.ids.switch_id(switch_label=switch_label)),
                Label(switch_label),
                classes=Tcss.switch_with_label,
            )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        expand_managed_switch = self.query_one(self.ids.switch.expand_managed_q, Switch)
        show_unchanged_switch = self.query_one(self.ids.switch.show_unchanged_q, Switch)
        show_unmanaged_switch = self.query_one(self.ids.switch.show_unmanaged_q, Switch)
        show_unwanted_switch = self.query_one(self.ids.switch.show_unwanted_q, Switch)
        switch_state = (
            expand_managed_switch.value,
            show_unchanged_switch.value,
            show_unmanaged_switch.value,
            show_unwanted_switch.value,
        )
        if show_unwanted_switch.value is True:
            show_unmanaged_switch.disabled = True
        else:
            show_unmanaged_switch.disabled = False
        self.post_message(ShowTreeQidMsg(self.state_to_tree_map[switch_state]))


class TabButtons(Horizontal):
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.labels = labels
        self.app_ids = app_ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            with Vertical(classes=Tcss.single_button_vertical):
                yield Button(
                    id=self.app_ids.btn_id(btn_label=btn_label),
                    label=btn_label,
                    classes=Tcss.tab_button,
                )

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_tab_btn)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
