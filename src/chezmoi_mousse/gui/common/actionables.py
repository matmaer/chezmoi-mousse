from __future__ import annotations

from typing import TYPE_CHECKING

from textual import getters, on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Label, Switch

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.enum_data import SwitchEnum
from chezmoi_mousse.functions import Commands
from chezmoi_mousse.str_enums import (
    FlatBtnLabel,
    OpBtnLabel,
    TabLabel,
    Tcss,
)

from .messages import (
    DirContentBtnMsg,
    DryRunBtnMsg,
    ExitModalBtnMsg,
    RefreshBtnMsg,
    ReviewBtnMsg,
    RunBtnMsg,
    TabBtnMsg,
)

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = [
    "DirContentBtn",
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
    def __init__(self, *, label: str, path: Path, app_ids: AppIds) -> None:
        super().__init__(label=label)
        self.path = path
        self.app_ids = app_ids

    @on(Button.Pressed)
    def _send_message(self, event: DirContentBtn.Pressed) -> None:
        event.stop()
        self.post_message(DirContentBtnMsg(self))


class DryRunBtn(Button):
    def __init__(self, btn_label: OpBtnLabel) -> None:
        super().__init__(
            classes=Tcss.operate_button,
            label=btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: DryRunBtn.Pressed) -> None:
        event.stop()
        self.post_message(DryRunBtnMsg(self))


class ExitModalBtn(Button):
    def __init__(self, btn_label: OpBtnLabel) -> None:
        super().__init__(
            classes=Tcss.operate_button,
            label=btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: ExitModalBtn.Pressed) -> None:
        event.stop()
        self.post_message(ExitModalBtnMsg(self))


class FlatBtn(Button):
    def __init__(self, ids: AppIds, *, btn_label: FlatBtnLabel) -> None:
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=ids.flat_button_id(btn=btn_label),
            label=btn_label,
            variant="primary",
        )


class RefreshBtn(Button):
    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        self.btn_id = self.app_ids.op_btn.refresh_tree
        self.btn_q = self.app_ids.op_btn.refresh_tree_q
        super().__init__(
            classes=Tcss.refresh_button,
            id=app_ids.op_btn.refresh_tree,
            label=OpBtnLabel.refresh_trees,
        )

    @on(Button.Pressed)
    def _send_message(self, event: RefreshBtn.Pressed) -> None:
        event.stop()
        self.post_message(RefreshBtnMsg(self))


class ReviewBtn(Button):
    def __init__(self, app_ids: AppIds, btn_label: OpBtnLabel) -> None:
        self.app_ids = app_ids
        self.btn_label = btn_label
        super().__init__(
            classes=Tcss.operate_button,
            id=self.app_ids.op_btn_id(operation=btn_label),
            label=btn_label,
        )

    @on(Button.Pressed)
    def _send_message(self, event: ReviewBtn.Pressed) -> None:
        event.stop()
        self.post_message(ReviewBtnMsg(self))


class RunBtn(Button):
    def __init__(self, btn_label: OpBtnLabel) -> None:
        super().__init__(label=btn_label, classes=Tcss.operate_button)

    @on(Button.Pressed)
    def _send_message(self, event: RunBtn.Pressed) -> None:
        event.stop()
        self.post_message(RunBtnMsg(self))


class TabBtn(Button):
    def __init__(self, *, app_ids: AppIds, label: TabLabel) -> None:
        super().__init__(classes=Tcss.tab_button, label=label)
        self.app_ids = app_ids

    @on(Button.Pressed)
    def _send_message(self, event: TabBtn.Pressed) -> None:
        event.stop()
        self.post_message(TabBtnMsg(self))


class FlatButtonsVertical(Vertical):
    def __init__(self, ids: AppIds, *, labels: tuple[FlatBtnLabel, ...]) -> None:
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.labels: tuple[FlatBtnLabel, ...] = labels

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield FlatBtn(self.ids, btn_label=label)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatBtn.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatBtn.Pressed) -> None:
        for btn in self.query(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class ReviewBtnGroup(HorizontalGroup):
    def __init__(self, app_ids: AppIds, labels: tuple[OpBtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels = labels
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield ReviewBtn(self.app_ids, btn_label=btn_label)


class RunBtnGroup(HorizontalGroup):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self, btn_labels: tuple[OpBtnLabel, ...]) -> None:
        self.btn_labels = btn_labels
        super().__init__(classes=Tcss.op_btn_group)

    def compose(self) -> ComposeResult:
        for btn_label in self.btn_labels:
            if btn_label in OpBtnLabel.dry_run_set():
                yield DryRunBtn(btn_label)
            elif btn_label in OpBtnLabel.run_btn_set():
                yield RunBtn(btn_label=btn_label)
            elif btn_label in OpBtnLabel.exit_modal_set():
                yield ExitModalBtn(btn_label)

    @on(DryRunBtnMsg)
    def _update_dry_run_btn_label(self) -> None:
        dry_run_btn = self.query_exactly_one(DryRunBtn)
        dry_run_btn.label = Commands.get_dry_run_btn_label()


class SwitchWithLabel(HorizontalGroup):
    def __init__(self, ids: AppIds, *, switch_enum: SwitchEnum) -> None:
        super().__init__()
        self.switch_enum = switch_enum
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Switch(id=self.ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class SwitchSlider(VerticalGroup):
    def __init__(self, ids: AppIds) -> None:
        super().__init__(id=ids.switch_slider, classes="-visible")
        if ids.tab_label in (TabLabel.apply, TabLabel.re_add):
            self.switches = (
                SwitchEnum.show_unchanged,
                SwitchEnum.show_unmanaged,
                SwitchEnum.expand_all,
            )
        else:  # for the AddTab
            self.switches = (SwitchEnum.show_managed, SwitchEnum.show_unwanted)
        self.ids = ids

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            yield SwitchWithLabel(self.ids, switch_enum=switch_enum)

    def on_mount(self) -> None:
        self.query_children(HorizontalGroup).last().styles.padding = 0


class TabButtons(Horizontal):
    def __init__(self, ids: AppIds, buttons: tuple[TabLabel, ...]) -> None:
        self.buttons = buttons
        self.tab_ids = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield TabBtn(app_ids=self.tab_ids, label=btn_enum)

    def on_mount(self) -> None:
        self.query(TabBtn).first().add_class(Tcss.last_clicked_tab_btn)

    @on(TabBtnMsg)
    def update_tcss_classes(self, event: TabBtn.Pressed) -> None:
        # dont call event.stop() because it's also processed in the content switcher
        for btn in self.query(TabBtn).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
