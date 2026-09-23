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
from chezmoi_mousse.gui.common.messages import (
    FlatBtnMsg,
    OperateBtnMsg,
    ShowTreeQidMsg,
    TabBtnMsg,
)
from chezmoi_mousse.str_enums import LabelStr, Tcss

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.message import Message

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.str_enums import BtnLabel


__all__ = [
    "FlatBtn",
    "FlatButtonsVertical",
    "OperateBtn",
    "OperateBtnGroup",
    "TabBtn",
    "TabButtons",
]


class _BaseAppButton(Button):
    def __init__(
        self,
        *,
        app_ids: AppIds,
        btn_label: BtnLabel,
        classes: str | None = None,
        flat: bool = False,
    ) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            label=self.btn_label,
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            classes=classes,
            flat=flat,
        )

    def send_message(self, event: Button.Pressed) -> Message: ...

    @on(Button.Pressed)
    def _handle_press(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(self.send_message(event))


class FlatBtn(_BaseAppButton):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        super().__init__(
            app_ids=app_ids,
            btn_label=btn_label,
            classes=Tcss.flat_button,
            flat=True,
        )

    def send_message(self, event: Button.Pressed) -> FlatBtnMsg:
        return FlatBtnMsg(
            button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
        )


class OperateBtn(_BaseAppButton):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        super().__init__(
            app_ids=app_ids,
            btn_label=btn_label,
            classes=Tcss.operate_button,
        )

    def send_message(self, event: Button.Pressed) -> OperateBtnMsg:
        return OperateBtnMsg(
            button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
        )


class TabBtn(_BaseAppButton):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        super().__init__(
            app_ids=app_ids,
            btn_label=btn_label,
            classes=Tcss.tab_button,
        )

    def send_message(self, event: Button.Pressed) -> TabBtnMsg:
        return TabBtnMsg(
            button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
        )


class FlatButtonsVertical(Container):
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels: tuple[BtnLabel, ...] = labels
        super().__init__(id=app_ids.container.flat_buttons)

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield FlatBtn(app_ids=self.app_ids, btn_label=label)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatBtnMsg)
    def update_tcss_classes(self, msg: FlatBtnMsg) -> None:
        for btn in self.query_children(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        msg.button.add_class(Tcss.last_clicked_flat_btn)


class OperateBtnGroup(HorizontalGroup):
    def __init__(self, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels = labels
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield OperateBtn(app_ids=self.app_ids, btn_label=btn_label)


class SwitchGroup(VerticalGroup):
    state_to_tree_map: ClassVar[dict[tuple[bool, ...], str]] = {
        # Managed trees including only paths with a status or meta status
        (False, False, False, False): store.op_ids.tree.managed_only_sp_q,
        (True, False, False, False): store.op_ids.tree.managed_only_sp_xpd_q,
        # Managed trees including all managed maths
        (False, True, False, False): store.op_ids.tree.managed_all_mp_q,
        (True, True, False, False): store.op_ids.tree.managed_all_mp_xpd_q,
        # Unmanaged trees
        (False, False, True, False): store.op_ids.tree.un_man_plus_sp_q,
        (False, True, True, False): store.op_ids.tree.un_man_plus_amp_q,
        # Unmanaged trees XPD
        (True, False, True, False): store.op_ids.tree.un_man_plus_sp_xpd_q,
        (True, True, True, False): store.op_ids.tree.un_man_plus_amp_xpd_q,
        # Uwwanted trees: show_unmanaged is False
        (False, False, False, True): store.op_ids.tree.un_wanted_plus_sp_q,
        (False, True, False, True): store.op_ids.tree.un_wanted_plus_amp_q,
        (True, False, False, True): store.op_ids.tree.un_wanted_plus_sp_xpd_q,
        (True, True, False, True): store.op_ids.tree.un_wanted_plus_amp_xpd_q,
        # Uwwanted trees: show_unmanaged is True
        (False, False, True, True): store.op_ids.tree.un_wanted_plus_sp_q,
        (False, True, True, True): store.op_ids.tree.un_wanted_plus_amp_q,
        (True, False, True, True): store.op_ids.tree.un_wanted_plus_sp_xpd_q,
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
        changed_switch = event.switch
        self.notify(f"changed switch {changed_switch}")
        switch_state = (
            self.query_one(self.ids.switch.expand_managed_q, Switch).value,
            self.query_one(self.ids.switch.show_unchanged_q, Switch).value,
            self.query_one(self.ids.switch.show_unmanaged_q, Switch).value,
            self.query_one(self.ids.switch.show_unwanted_q, Switch).value,
        )
        self.post_message(ShowTreeQidMsg(self.state_to_tree_map[switch_state]))


class TabButtons(Horizontal):
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.labels = labels
        self.app_ids = app_ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            with Vertical(classes=Tcss.single_button_vertical):
                yield TabBtn(app_ids=self.app_ids, btn_label=btn_label)

    def on_mount(self) -> None:
        self.query(TabBtn).first().add_class(Tcss.last_clicked_tab_btn)

    @on(TabBtnMsg)
    def update_tcss_classes(self, msg: TabBtnMsg) -> None:
        for btn in self.query(TabBtn).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        msg.button.add_class(Tcss.last_clicked_tab_btn)
