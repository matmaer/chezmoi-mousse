from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import on
from textual.containers import Container, Horizontal, HorizontalGroup, VerticalGroup
from textual.widgets import Button, Label, Switch

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
from chezmoi_mousse.str_enums import BtnLabel, LabelStr, Tcss

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds


__all__ = [
    "FlatButtonsVertical",
    "OperateBtnGroup",
    "PromptBtnGroup",
    "SwitchGroup",
    "TabButtons",
    "TreeButtons",
]


class FlatButtonsVertical(Container):
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.labels: tuple[BtnLabel, ...] = labels
        super().__init__(id=app_ids.container.flat_buttons)

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield Button(label=label, flat=True)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query_children(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class OperateBtnGroup(HorizontalGroup):
    def __init__(self, labels: tuple[BtnLabel, ...]) -> None:
        self.labels = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield Button(label=btn_label)

    def on_mount(self) -> None:
        buttons = self.query_children(Button).results()
        for btn in buttons:
            if btn.label in (
                BtnLabel.chezmoi_add,
                BtnLabel.chezmoi_destroy,
                BtnLabel.chezmoi_forget,
            ):
                btn.disabled = True
            elif btn.label in (
                BtnLabel.start_auto_log,
                BtnLabel.stop_auto_log,
                BtnLabel.log_memory,
            ):
                btn.disabled = btn.label == BtnLabel.start_auto_log
                btn.display = False


class PromptBtnGroup(HorizontalGroup):
    def __init__(self, labels: tuple[str, ...]) -> None:
        self.labels = labels
        super().__init__(classes=Tcss.prompt_btn_group)

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield Button(label=btn_label)

    def on_mount(self) -> None:
        buttons = self.query_children(Button)
        for btn in buttons:
            btn.display = False


class TreeButtons(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button(label=BtnLabel.dest_dir, classes=Tcss.dest_dir_button)
        yield Button(
            label=BtnLabel.expand, classes=Tcss.tree_op_button, tooltip="expand leaves"
        )
        yield Button(
            label=BtnLabel.collapse,
            classes=Tcss.tree_op_button,
            tooltip="collapse leaves",
        )
        yield Button(
            label=BtnLabel.refresh, classes=Tcss.tree_op_button, tooltip="refresh tree"
        )


class SwitchGroup(VerticalGroup):
    state_to_tree_map: ClassVar[dict[tuple[bool, ...], str]] = {
        # Managed trees including only paths with a status or meta status
        (False, False, False): store.op_ids.tree.managed_sp_q,
        # Managed trees including all managed maths
        (True, False, False): store.op_ids.tree.managed_amp_q,
        # Un-managed trees (show_unchanged is False)
        (False, True, False): store.op_ids.tree.wanted_plus_sp_q,
        # Un-managed trees (show_unchanged is True)
        (True, True, False): store.op_ids.tree.wanted_plus_amp_q,
        # Unwanted trees when show_unchanged is False (show_unmanaged switch disabled)
        (False, True, True): store.op_ids.tree.un_wanted_plus_sp_q,
        (False, False, True): store.op_ids.tree.un_wanted_plus_sp_q,
        # Unwanted trees when show_unchanged is True (show_unmanaged switch disabled)
        (True, False, True): store.op_ids.tree.un_wanted_plus_amp_q,
        (True, True, True): store.op_ids.tree.un_wanted_plus_amp_q,
    }

    def compose(self) -> ComposeResult:
        for switch_label in (
            LabelStr.show_unchanged,
            LabelStr.show_unmanaged,
            LabelStr.show_unwanted,
        ):
            yield HorizontalGroup(
                Switch(id=store.op_ids.switch_id(switch_label=switch_label)),
                Label(switch_label),
                classes=Tcss.switch_with_label,
            )

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        show_unchanged_switch = self.query_one(
            store.op_ids.switch.show_unchanged_q, Switch
        )
        show_unmanaged_switch = self.query_one(
            store.op_ids.switch.show_unmanaged_q, Switch
        )
        show_unwanted_switch = self.query_one(
            store.op_ids.switch.show_unwanted_q, Switch
        )
        switch_state = (
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
    def __init__(self, *, labels: tuple[BtnLabel, ...]) -> None:
        self.labels = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield Button(label=btn_label, classes=Tcss.tab_button)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_tab_btn)

    @on(Button.Pressed)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
