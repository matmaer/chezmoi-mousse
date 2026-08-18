from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Label, Switch

from chezmoi_mousse.enum_data import OpBtnEnum, SwitchEnum
from chezmoi_mousse.str_enums import FlatBtnLabel, OpBtnLabel, TabLabel, Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.app_ids import AppIds


__all__ = [
    "DirContentBtn",
    "FlatButton",
    "FlatButtonsVertical",
    "OpButton",
    "OperateButtons",
    "RefreshTreeButton",
    "SwitchSlider",
    "TabButton",
    "TabButtons",
]


class DirContentBtn(Button):
    def __init__(self, *, label: str, path: Path, app_ids: AppIds) -> None:
        super().__init__(label=label)
        self.path = path
        self.app_ids = app_ids


class FlatButton(Button):
    def __init__(self, ids: AppIds, *, btn_label: FlatBtnLabel) -> None:
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=ids.flat_button_id(btn=btn_label),
            label=btn_label,
            variant="primary",
        )


class FlatButtonsVertical(Vertical):
    def __init__(self, ids: AppIds, *, labels: tuple[FlatBtnLabel, ...]) -> None:
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.labels: tuple[FlatBtnLabel, ...] = labels

    def compose(self) -> ComposeResult:
        for label in self.labels:
            yield FlatButton(self.ids, btn_label=label)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatButton.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatButton.Pressed) -> None:
        for btn in self.query(Button).results():
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class CancelButton(Button):
    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        super().__init__(
            classes=Tcss.operate_button,
            id=self.app_ids.op_btn.cancel,
            label=OpBtnLabel.cancel,
        )


class RefreshTreeButton(Button):
    def __init__(self, app_ids: AppIds) -> None:
        self.app_ids = app_ids
        super().__init__(
            classes=Tcss.refresh_button,
            id=self.app_ids.op_btn.refresh_tree,
            label=OpBtnLabel.refresh_tree,
        )


class OpButton(Button):
    def __init__(self, *, btn_id: str, btn_enum: OpBtnEnum, app_ids: AppIds) -> None:
        super().__init__(classes=Tcss.operate_button, id=btn_id, label=btn_enum.label)
        self.btn_enum: OpBtnEnum = btn_enum
        self.btn_id: str = btn_id
        self.app_ids = app_ids
        if btn_enum in (
            OpBtnEnum.destroy_review,
            OpBtnEnum.forget_review,
            OpBtnEnum.add_review,
        ):
            self.disabled = True
        elif btn_enum in (
            OpBtnEnum.add_run,
            OpBtnEnum.apply_run,
            OpBtnEnum.destroy_run,
            OpBtnEnum.forget_run,
            OpBtnEnum.re_add_run,
        ):
            self.display = False


class OperateButtons(HorizontalGroup):
    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        super().__init__(id=ids.container.operate_buttons, classes=Tcss.op_btn_group)

    def compose(self) -> ComposeResult:
        for btn_id, btn_enum in self.app_ids.op_btn_map.items():
            yield OpButton(btn_id=btn_id, btn_enum=btn_enum, app_ids=self.app_ids)
        yield CancelButton(app_ids=self.app_ids)

    def on_mount(self) -> None:
        cancel_btn = self.query_one(self.app_ids.op_btn.cancel_q, CancelButton)
        cancel_btn.display = False

    def set_path_arg(self, path: Path) -> None:
        for btn_enum in self.app_ids.op_btn_map.values():
            btn_enum.path_arg = path


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


class TabButton(Button):
    def __init__(self, *, app_ids: AppIds, label: TabLabel) -> None:
        super().__init__(classes=Tcss.tab_button, label=label)
        self.app_ids = app_ids


class TabButtons(Horizontal):
    def __init__(self, ids: AppIds, buttons: tuple[TabLabel, ...]) -> None:
        self.buttons = buttons
        self.tab_ids = ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield TabButton(app_ids=self.tab_ids, label=btn_enum)

    def on_mount(self) -> None:
        self.query(TabButton).first().add_class(Tcss.last_clicked_tab_btn)

    @on(TabButton.Pressed)
    def update_tcss_classes(self, event: TabButton.Pressed) -> None:
        for btn in self.query(TabButton).results():
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
