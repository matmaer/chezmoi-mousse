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

from chezmoi_mousse.enum_data import SwitchEnum
from chezmoi_mousse.str_enums import (
    BtnLabel,
    Tcss,
)

from .messages import (
    DebugBtnMsg,
    DirContentBtnMsg,
    DryRunBtnMsg,
    ExitModalBtnMsg,
    FlatBtnMsg,
    RefreshBtnMsg,
    ReviewBtnMsg,
    RunBtnMsg,
    TabBtnMsg,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult

    from chezmoi_mousse.app_ids import AppIds


__all__ = [
    "DirContentBtn",
    "DryRunBtn",
    "FlatBtn",
    "RefreshBtn",
    "ReviewBtn",
    "TabBtn",
    "FlatButtonsVertical",
    "ReviewBtnGroup",
    "RunBtnGroup",
    "SwitchSlider",
    "TabButtons",
]


class DirContentBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: str, path: Path) -> None:
        super().__init__(label=btn_label)
        self.path = path
        self.app_ids = app_ids

    @on(Button.Pressed)
    def _send_message(self, event: DirContentBtn.Pressed) -> None:
        event.stop()
        self.post_message(DirContentBtnMsg(self))


class DebugBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        super().__init__(
            id=app_ids.btn_id(btn_label=btn_label),
            label=btn_label,
            classes=Tcss.operate_button,
        )

    @on(Button.Pressed)
    def _send_message(self, event: DebugBtn.Pressed) -> None:
        event.stop()
        self.post_message(DebugBtnMsg(self))


class DryRunBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        super().__init__(
            label=btn_label,
            classes=Tcss.operate_button,
        )

    @on(Button.Pressed)
    def _send_message(self, event: DryRunBtn.Pressed) -> None:
        event.stop()
        self.post_message(DryRunBtnMsg(self))


class ExitModalBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        super().__init__(
            classes=Tcss.operate_button,
            label=btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: ExitModalBtn.Pressed) -> None:
        event.stop()
        self.post_message(ExitModalBtnMsg(self))


class FlatBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.btn_label = btn_label
        self.app_ids = app_ids
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
            variant="primary",
        )

    @on(Button.Pressed)
    def _send_message(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(FlatBtnMsg(self))


class RefreshBtn(Button):
    def __init__(self, *, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        self.btn_label = BtnLabel.refresh_trees
        super().__init__(
            classes=Tcss.refresh_button,
            id=self.app_ids.op_btn.refresh_tree,
            label=self.btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: RefreshBtn.Pressed) -> None:
        event.stop()
        self.post_message(RefreshBtnMsg(self))


class ReviewBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            classes=Tcss.operate_button,
            id=self.app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: ReviewBtn.Pressed) -> None:
        event.stop()
        self.post_message(ReviewBtnMsg(self.app_ids.tab_label, self))


class RunBtn(Button):
    def __init__(self, *, app_ids: AppIds, btn_label: BtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            classes=Tcss.operate_button,
            id=app_ids.btn_id(btn_label=self.btn_label),
            label=self.btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: RunBtn.Pressed) -> None:
        event.stop()
        self.post_message(RunBtnMsg(self))


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
        self.post_message(TabBtnMsg(self))


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


class ReviewBtnGroup(HorizontalGroup):
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels = labels
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield ReviewBtn(app_ids=self.app_ids, btn_label=btn_label)


class DebugBtnGroup(HorizontalGroup):
    def __init__(self, *, app_ids: AppIds, btn_labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.btn_labels = btn_labels
        super().__init__(classes=Tcss.op_btn_group)

    def compose(self) -> ComposeResult:
        for btn_label in self.btn_labels:
            yield DebugBtn(app_ids=self.app_ids, btn_label=btn_label)


class RunBtnGroup(HorizontalGroup):
    def __init__(self, *, app_ids: AppIds, btn_labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.btn_labels = btn_labels
        super().__init__(classes=Tcss.op_btn_group)

    def compose(self) -> ComposeResult:
        for btn_label in self.btn_labels:
            if btn_label in BtnLabel.dry_run_set():
                yield DryRunBtn(app_ids=self.app_ids, btn_label=btn_label)
            elif btn_label in BtnLabel.run_btn_set():
                yield RunBtn(app_ids=self.app_ids, btn_label=btn_label)
            elif btn_label in BtnLabel.exit_modal_set():
                yield ExitModalBtn(app_ids=self.app_ids, btn_label=btn_label)


class _SwitchWithLabel(HorizontalGroup):
    def __init__(self, *, app_ids: AppIds, switch_enum: SwitchEnum) -> None:
        super().__init__()
        self.switch_enum = switch_enum
        self.app_ids = app_ids

    def compose(self) -> ComposeResult:
        yield Switch(id=self.app_ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class SwitchSlider(VerticalGroup):
    def __init__(self, *, app_ids: AppIds) -> None:
        super().__init__(id=app_ids.switch_slider, classes="-visible")
        if app_ids.tab_label in (BtnLabel.apply, BtnLabel.re_add):
            self.switches: tuple[SwitchEnum, ...] = (
                SwitchEnum.show_unchanged,
                SwitchEnum.show_unmanaged,
                SwitchEnum.expand_all,
            )
        else:  # for the AddTab
            self.switches = (SwitchEnum.show_managed, SwitchEnum.show_unwanted)
        self.app_ids = app_ids

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            yield _SwitchWithLabel(app_ids=self.app_ids, switch_enum=switch_enum)

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
        for btn in self.query_children(TabBtn).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        msg.button.add_class(Tcss.last_clicked_tab_btn)
