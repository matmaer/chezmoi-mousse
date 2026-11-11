from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import on
from textual.containers import Horizontal, HorizontalGroup, VerticalGroup
from textual.widgets import Button, Label, Switch

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.messages import ShowTreeQidMsg
from chezmoi_mousse.str_enums import BtnLabel, LabelStr, Tcss

if TYPE_CHECKING:
    from textual.app import ComposeResult


__all__ = [
    "FlatBtnGroup",
    "OperateBtnGroup",
    "PromptBtnGroup",
    "SwitchGroup",
    "TreeBtnGroup",
]


class FlatBtnGroup(VerticalGroup):
    def __init__(self, *, labels: tuple[BtnLabel, ...]) -> None:
        self.labels: tuple[BtnLabel, ...] = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield Button(label=label, flat=True, classes=Tcss.flat_btn)

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
            yield Button(label=btn_label, classes=Tcss.operate_btn)

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
            elif btn.label == BtnLabel.create_paths:
                btn.tooltip = "Create all missing test paths"
            elif btn.label == BtnLabel.remove_paths:
                btn.tooltip = "Remove all existing test paths"


class PromptBtnGroup(HorizontalGroup):
    def __init__(self, labels: tuple[str, ...]) -> None:
        self.labels = labels
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield Button(label=btn_label, classes=Tcss.prompt_btn)

    def on_mount(self) -> None:
        buttons = self.query_children(Button)
        for btn in buttons:
            btn.display = False


class TreeBtnGroup(Horizontal):
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

    def on_mount(self) -> None:
        for btn in self.query_children(Button):
            if btn.label == BtnLabel.expand:
                self.expand_btn = btn
            elif btn.label == BtnLabel.collapse:
                self.collapse_btn = btn


class SwitchGroup(VerticalGroup):
    state_to_tree_map: ClassVar[dict[tuple[bool, ...], str]] = {
        # Managed trees including only paths with a status or meta status
        (False, False, False): store.op_ids.tree.managed_sp_q,
        # Managed trees including all managed maths
        (True, False, False): store.op_ids.tree.managed_amp_q,
        # Un-managed trees (show_unchanged is False)
        (False, True, False): store.op_ids.tree.filtered_unman_sp_q,
        # Un-managed trees (show_unchanged is True)
        (True, True, False): store.op_ids.tree.filtered_unman_amp_q,
        # Extended tree
        (False, True, True): store.op_ids.tree.extended_q,
        (False, False, True): store.op_ids.tree.extended_q,
        (True, False, True): store.op_ids.tree.extended_q,
        (True, True, True): store.op_ids.tree.extended_q,
    }

    def compose(self) -> ComposeResult:
        yield HorizontalGroup(
            Switch(id=store.op_ids.switch.show_unchanged, name=LabelStr.show_unchanged),
            Label(LabelStr.show_unchanged),
            classes=Tcss.switch_with_label,
        )
        yield HorizontalGroup(
            Switch(id=store.op_ids.switch.show_unmanaged, name=LabelStr.show_unmanaged),
            Label(LabelStr.show_unmanaged),
            classes=Tcss.switch_with_label,
        )
        yield HorizontalGroup(
            Switch(id=store.op_ids.switch.extended_view, name=LabelStr.extended_view),
            Label(LabelStr.extended_view),
            classes=Tcss.switch_with_label,
        )

    def on_mount(self) -> None:
        self.show_unchanged = self.query_one(
            store.op_ids.switch.show_unchanged_q, Switch
        )
        self.show_unmanaged = self.query_one(
            store.op_ids.switch.show_unmanaged_q, Switch
        )
        self.extended_view = self.query_one(store.op_ids.switch.extended_view_q, Switch)

    @on(Switch.Changed)
    def handle_tree_switches(self, event: Switch.Changed) -> None:
        event.stop()
        switch_state = (
            self.show_unchanged.value,
            self.show_unmanaged.value,
            self.extended_view.value,
        )
        if self.extended_view.value is True:
            self.show_unchanged.disabled = True
            self.show_unmanaged.disabled = True
        else:
            self.show_unchanged.disabled = False
            self.show_unmanaged.disabled = False
        self.post_message(ShowTreeQidMsg(self.state_to_tree_map[switch_state]))
