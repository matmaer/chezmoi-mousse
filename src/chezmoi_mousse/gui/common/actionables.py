from collections.abc import Mapping
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button, Label, Link, Switch

from chezmoi_mousse import (
    AppType,
    FlatBtnLabel,
    LinkBtn,
    OpBtnEnum,
    OpBtnLabel,
    SubTabLabel,
    SwitchEnum,
    TabName,
    Tcss,
)

from .messages import OperateButtonMsg

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds


__all__ = [
    "FlatButton",
    "FlatButtonsVertical",
    "FlatLink",
    "TabButtons",
    "OpButton",
    "OperateButtons",
    "SwitchWithLabel",
    "SwitchSlider",
]


class FlatButton(Button):
    def __init__(self, ids: "AppIds", *, btn_enum: FlatBtnLabel) -> None:
        super().__init__(
            classes=Tcss.flat_button,
            flat=True,
            id=ids.flat_button_id(btn=btn_enum),
            label=btn_enum,
            variant="primary",
        )


class FlatLink(Link):
    def __init__(self, link_enum: LinkBtn) -> None:
        super().__init__(text=link_enum.link_text, url=link_enum.link_url)
        self.link_enum = link_enum

    def on_mount(self) -> None:
        if self.link_enum == LinkBtn.chezmoi_guess:
            self.add_class(Tcss.guess_link)


class FlatButtonsVertical(Vertical):

    def __init__(self, ids: "AppIds", *, buttons: tuple[FlatBtnLabel, ...]) -> None:
        super().__init__(id=ids.container.left_side, classes=Tcss.tab_left_vertical)
        self.ids = ids
        self.buttons: tuple[FlatBtnLabel, ...] = buttons

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            yield FlatButton(self.ids, btn_enum=btn_enum)

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_flat_btn)

    @on(FlatButton.Pressed, Tcss.flat_button.dot_prefix)
    def update_tcss_classes(self, event: FlatButton.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_flat_btn)
        event.button.add_class(Tcss.last_clicked_flat_btn)


class OpButton(Button, AppType):

    def __init__(self, *, btn_id: str, btn_enum: OpBtnEnum | OpBtnLabel) -> None:
        if isinstance(btn_enum, OpBtnEnum):
            label = btn_enum.label
        else:
            label = btn_enum.value
        super().__init__(classes=Tcss.operate_button, id=btn_id, label=label)
        self.btn_enum: OpBtnEnum | OpBtnLabel = btn_enum


class OperateButtons(HorizontalGroup):
    def __init__(
        self, ids: "AppIds", *, btn_dict: Mapping[str, OpBtnEnum | OpBtnLabel]
    ) -> None:
        super().__init__(id=ids.container.operate_buttons)
        self.ids = ids
        self.btn_dict = btn_dict

    def compose(self) -> ComposeResult:
        for btn_id, btn_enum in self.btn_dict.items():
            yield OpButton(btn_id=btn_id, btn_enum=btn_enum)

    def on_mount(self) -> None:
        if self.ids.canvas_name == TabName.debug:
            return
        self.close_btn = self.query_one(self.ids.op_btn.close_q, OpButton)
        self.close_btn.display = False
        all_buttons: list[OpButton] = [
            b for b in self.query_children().results() if isinstance(b, OpButton)
        ]
        self.all_cmd_buttons = [b for b in all_buttons if b != self.close_btn]
        self.all_btn_ids: list[str]

    def _get_other_op_cmd_buttons(self, btn_id: str) -> list[OpButton]:
        return [b for b in self.all_cmd_buttons if btn_id != b.id and b.id is not None]

    @on(Button.Pressed)
    def update_button_display(self, event: Button.Pressed) -> None:
        # we never toggle display or change labels in the debug tab
        if self.ids.canvas_name == TabName.debug:
            return
        if event.button.id == self.ids.op_btn.close:
            self.close_btn.display = False
        elif event.button not in self.all_cmd_buttons:
            self.close_btn.display = True
            for btn in self.all_cmd_buttons:
                btn.display = True
        if event.button in self.all_cmd_buttons and "Review" in str(event.button.label):
            for btn in [b for b in self.all_cmd_buttons if event.button.id != b.id]:
                btn.display = False
            self.close_btn.display = True
        elif event.button in self.all_cmd_buttons and "Run" in str(event.button.label):
            event.button.disabled = True
        if isinstance(event.button, OpButton):
            self.post_message(OperateButtonMsg(self.ids, button=event.button))


class SwitchWithLabel(HorizontalGroup):

    def __init__(self, ids: "AppIds", *, switch_enum: "SwitchEnum") -> None:
        super().__init__()
        self.switch_enum = switch_enum
        self.ids = ids

    def compose(self) -> ComposeResult:
        yield Switch(id=self.ids.switch_id(switch=self.switch_enum))
        yield Label(self.switch_enum.label).with_tooltip(
            tooltip=self.switch_enum.enabled_tooltip
        )


class SwitchSlider(VerticalGroup):
    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.container.switch_slider, classes="-visible")
        if ids.canvas_name in (TabName.apply, TabName.re_add):
            self.switches = (SwitchEnum.unchanged, SwitchEnum.expand_all)
        else:  # for the AddTab
            self.switches = (SwitchEnum.unmanaged_dirs, SwitchEnum.unwanted)
        self.ids = ids

    def compose(self) -> ComposeResult:
        for switch_enum in self.switches:
            yield SwitchWithLabel(self.ids, switch_enum=switch_enum)

    def on_mount(self) -> None:
        self.query_children(HorizontalGroup).last().styles.padding = 0


class TabButtons(Horizontal):
    def __init__(self, ids: "AppIds", *, buttons: tuple[SubTabLabel, ...]):
        super().__init__()
        self.ids = ids
        self.buttons = buttons

    def compose(self) -> ComposeResult:
        for btn_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical):
                yield Button(
                    label=btn_enum,
                    id=self.ids.tab_button_id(btn=btn_enum),
                    classes=Tcss.tab_button,
                )

    def on_mount(self) -> None:
        self.query(Button).first().add_class(Tcss.last_clicked_tab_btn)

    @on(Button.Pressed, Tcss.tab_button.dot_prefix)
    def update_tcss_classes(self, event: Button.Pressed) -> None:
        for btn in self.query(Button):
            btn.remove_class(Tcss.last_clicked_tab_btn)
        event.button.add_class(Tcss.last_clicked_tab_btn)
