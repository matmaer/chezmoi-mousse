from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
    VerticalGroup,
)
from textual.widgets import Button, Label, Switch

from chezmoi_mousse.gui.common.messages import (
    DirContentBtnMsg,
    DryRunBtnMsg,
    FlatBtnMsg,
    OperateBtnMsg,
    RefreshBtnMsg,
    TabBtnMsg,
)
from chezmoi_mousse.str_enums import BtnLabel, LabelStr, Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds


__all__ = [
    "DebugBtn",
    "DirContentBtn",
    "DryRunBtn",
    "FlatBtn",
    "FlatButtonsVertical",
    "OperateBtnGroup",
    "RefreshBtn",
    "SwitchSlider",
    "TabBtn",
    "TabButtons",
]


class DirContentBtn(Button):
    def __init__(
        self, button: Button, app_ids: AppIds, btn_label: BtnLabel, *, path: Path
    ) -> None:
        self.button = button
        self.app_ids = app_ids
        self.btn_label = btn_label
        self.path = path
        super().__init__(
            id=self.app_ids.btn_id(btn_label=self.btn_label), label=self.btn_label
        )

    @on(Button.Pressed)
    def _send_message(self, event: DirContentBtn.Pressed) -> None:
        event.stop()
        self.post_message(
            DirContentBtnMsg(
                self.button,
                self.app_ids,
                self.btn_label,
                path=self.path,
            )
        )


class DebugBtn(Button):
    def __init__(self, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
            classes=Tcss.operate_button,
        )

    @on(Button.Pressed)
    def _send_message(self, event: DebugBtn.Pressed) -> None:
        event.stop()
        self.post_message(OperateBtnMsg(event.button, self.app_ids, self.btn_label))


class DryRunBtn(Button):
    def __init__(self, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
            classes=Tcss.operate_button,
        )

    @on(Button.Pressed)
    def _send_message(self, event: DryRunBtn.Pressed) -> None:
        event.stop()
        self.post_message(
            DryRunBtnMsg(button=self, app_ids=self.app_ids, btn_label=self.btn_label)
        )


class FlatBtn(Button):
    def __init__(self, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.btn_label = btn_label
        self.app_ids = app_ids
        super().__init__(
            flat=True,
            variant="primary",
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
            classes=Tcss.flat_button,
        )

    @on(Button.Pressed)
    def _send_message(self, event: FlatBtn.Pressed) -> None:
        event.stop()
        self.post_message(
            FlatBtnMsg(
                button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
            )
        )


class RefreshBtn(Button):
    def __init__(self, *, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        self.btn_label = BtnLabel.refresh_trees
        super().__init__(
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
            classes=Tcss.refresh_button,
        )

    @on(Button.Pressed)
    def _send_message(self, event: RefreshBtn.Pressed) -> None:
        event.stop()
        self.post_message(
            RefreshBtnMsg(
                button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
            )
        )


class OperateBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            classes=Tcss.operate_button,
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(
            OperateBtnMsg(
                button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
            )
        )


class TabBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.btn_label = btn_label
        self.app_ids = app_ids
        super().__init__(
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            classes=Tcss.tab_button,
            label=self.btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: TabBtn.Pressed) -> None:
        event.stop()
        self.post_message(
            TabBtnMsg(
                button=event.button, app_ids=self.app_ids, btn_label=self.btn_label
            )
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
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels = labels
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield OperateBtn(app_ids=self.app_ids, btn_label=btn_label)


class SwitchSlider(VerticalGroup):
    def __init__(self, *, app_ids: AppIds) -> None:
        super().__init__(id=app_ids.switch_slider, classes="-visible")
        if app_ids.tab_label in (BtnLabel.apply, BtnLabel.re_add):
            self.switches: tuple[LabelStr, ...] = (
                LabelStr.show_unchanged,
                LabelStr.show_unmanaged,
                LabelStr.expand_all,
            )
        else:  # for the AddTab
            self.switches = (LabelStr.show_managed, LabelStr.show_unwanted)
        self.app_ids = app_ids

    def compose(self) -> ComposeResult:
        for switch_label in self.switches:
            yield HorizontalGroup(
                Switch(id=self.app_ids.switch_id(switch_label=switch_label)),
                Label(switch_label),
            )

    def on_mount(self) -> None:
        self.query_children(HorizontalGroup).last().styles.padding = 0


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
