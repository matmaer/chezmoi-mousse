from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button

from chezmoi_mousse.constants import Area, TcssStr
from chezmoi_mousse.id_typing import (
    OperateButtons,
    TabButtons,
    TabIds,
    VerticalButtons,
)


class ButtonsHorizontal(HorizontalGroup):

    def __init__(
        self,
        *,
        tab_ids: TabIds,
        buttons: TabButtons | OperateButtons,
        area: Area,
    ) -> None:
        self.buttons = buttons
        self.area: Area = area
        self.tab_ids: TabIds = tab_ids
        super().__init__(id=self.tab_ids.buttons_horizontal_id(self.area))

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(
                id=self.tab_ids.button_vertical_id(button_enum),
                classes=TcssStr.single_button_vertical,
            ):
                yield Button(
                    label=button_enum.value,
                    id=self.tab_ids.button_id(btn=button_enum),
                )


class ButtonsVertical(VerticalGroup):

    def __init__(
        self, *, tab_ids: TabIds, buttons: VerticalButtons, area: Area
    ) -> None:
        self.buttons: VerticalButtons = buttons
        self.area: Area = area
        self.tab_ids: TabIds = tab_ids
        super().__init__(
            id=self.tab_ids.buttons_vertical_group_id(self.area),
            classes=TcssStr.navigate_buttons_vertical,
        )

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield Button(
                label=button_enum.value,
                variant="primary",
                flat=True,
                classes=TcssStr.navigate_button,
                id=self.tab_ids.button_id(btn=button_enum),
            )


class OperateBtnHorizontal(ButtonsHorizontal):
    def __init__(self, *, tab_ids: TabIds, buttons: OperateButtons):
        super().__init__(tab_ids=tab_ids, buttons=buttons, area=Area.bottom)

    def on_mount(self) -> None:
        self.add_class(TcssStr.operate_buttons_horizontal)
        self.query(Button).add_class(TcssStr.operate_button)


class TabBtnHorizontal(ButtonsHorizontal):
    def __init__(self, *, tab_ids: TabIds, buttons: TabButtons, area: Area):
        super().__init__(tab_ids=tab_ids, buttons=buttons, area=area)

    def on_mount(self) -> None:
        self.add_class(TcssStr.tab_buttons_horizontal)
        self.query(Button).add_class(TcssStr.tab_button)
        self.query_one(
            self.tab_ids.button_id("#", btn=self.buttons[0])
        ).add_class(TcssStr.last_clicked)

    @on(Button.Pressed, ".tab_button")
    def update_tab_btn_last_clicked(self, event: Button.Pressed) -> None:
        self.query(Button).remove_class(TcssStr.last_clicked)
        event.button.add_class(TcssStr.last_clicked)
