from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on
from textual.containers import (
    Container,
    Horizontal,
    HorizontalGroup,
    Vertical,
)
from textual.widgets import Button

from chezmoi_mousse import store
from chezmoi_mousse.gui.common.messages import (
    DestDirBtnMsg,
    DirContentBtnMsg,
    FlatBtnMsg,
    OperateBtnMsg,
    RefreshBtnMsg,
    TabBtnMsg,
)
from chezmoi_mousse.str_enums import BtnLabel, Chars, Tcss

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult
    from textual.message import Message

    from chezmoi_mousse.app_ids import AppIds


__all__ = [
    "DestDirBtn",
    "DirContentBtn",
    "FlatBtn",
    "FlatButtonsVertical",
    "OperateBtn",
    "OperateBtnGroup",
    "RefreshBtn",
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


class DestDirBtn(_BaseAppButton):
    def __init__(self, *, app_ids: AppIds) -> None:
        super().__init__(
            app_ids=app_ids,
            btn_label=BtnLabel.dest_dir_select,
            classes=Tcss.dest_dir_button,
        )

    def on_mount(self) -> None:
        self.label = (
            f"{Chars.big_down_triangle} {store.cfg.dest_dir} {Chars.big_down_triangle} "
        )

    def send_message(self, event: Button.Pressed) -> DestDirBtnMsg:
        return DestDirBtnMsg(
            button=event.button,
            tab_label=self.app_ids.tab_label,
        )


class DirContentBtn(_BaseAppButton):
    def __init__(self, app_ids: AppIds, btn_label: BtnLabel, *, path: Path) -> None:
        self.path = path
        super().__init__(app_ids=app_ids, btn_label=btn_label)

    def send_message(self, event: Button.Pressed) -> DirContentBtnMsg:
        return DirContentBtnMsg(
            event.button,
            self.app_ids,
            self.btn_label,
            path=self.path,
        )


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


class RefreshBtn(_BaseAppButton):
    def __init__(self, *, app_ids: AppIds) -> None:
        super().__init__(
            app_ids=app_ids,
            btn_label=BtnLabel.refresh_trees,
            classes=Tcss.refresh_button,
        )

    def send_message(self, event: Button.Pressed) -> RefreshBtnMsg:
        return RefreshBtnMsg(
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
    def __init__(self, *, app_ids: AppIds, labels: tuple[BtnLabel, ...]) -> None:
        self.app_ids = app_ids
        self.labels = labels
        super().__init__(
            id=app_ids.container.operate_buttons, classes=Tcss.op_btn_group
        )

    def compose(self) -> ComposeResult:
        for btn_label in self.labels:
            yield OperateBtn(app_ids=self.app_ids, btn_label=btn_label)


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
