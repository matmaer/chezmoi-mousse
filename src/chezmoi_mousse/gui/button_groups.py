from textual import on
from textual.app import ComposeResult
from textual.containers import HorizontalGroup, Vertical, VerticalGroup
from textual.widgets import Button

from chezmoi_mousse import Area, NavBtn, OperateBtn, TabBtn, Tcss
from chezmoi_mousse.gui import TabIds

__all__ = [
    "ButtonsHorizontal",
    "NavButtonsVertical",
    "OperateBtnHorizontal",
    "TabBtnHorizontal",
]


class ButtonsHorizontal(HorizontalGroup):

    def __init__(
        self,
        *,
        tab_ids: TabIds,
        buttons: tuple[TabBtn, ...] | tuple[OperateBtn, ...],
        area: Area,
    ) -> None:
        self.buttons = buttons
        self.area: Area = area
        self.tab_ids: TabIds = tab_ids
        super().__init__(id=self.tab_ids.buttons_horizontal_id(self.area))

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            with Vertical(classes=Tcss.single_button_vertical.name):
                yield Button(
                    label=button_enum.value,
                    id=self.tab_ids.button_id(btn=button_enum),
                )


class NavButtonsVertical(VerticalGroup):

    def __init__(
        self, *, tab_ids: TabIds, buttons: tuple[NavBtn, ...]
    ) -> None:
        self.buttons: tuple[NavBtn, ...] = buttons
        self.tab_ids: TabIds = tab_ids
        super().__init__()

    def compose(self) -> ComposeResult:
        for button_enum in self.buttons:
            yield Button(
                label=button_enum.value,
                variant="primary",
                flat=True,
                classes=Tcss.nav_button.name,
                id=self.tab_ids.button_id(btn=button_enum),
            )


class OperateBtnHorizontal(ButtonsHorizontal):
    def __init__(self, *, tab_ids: TabIds, buttons: tuple[OperateBtn, ...]):
        super().__init__(tab_ids=tab_ids, buttons=buttons, area=Area.bottom)

    def on_mount(self) -> None:
        for btn in self.query(Button):
            btn.add_class(Tcss.operate_button.name)
            btn.disabled = True


class TabBtnHorizontal(ButtonsHorizontal):
    def __init__(
        self, *, tab_ids: TabIds, buttons: tuple[TabBtn, ...], area: Area
    ):
        super().__init__(tab_ids=tab_ids, buttons=buttons, area=area)

    def on_mount(self) -> None:
        self.query(Button).add_class(Tcss.tab_button.name)
        self.query_one(
            self.tab_ids.button_id("#", btn=self.buttons[0])
        ).add_class(Tcss.last_clicked.name)

    @on(Button.Pressed, f".{Tcss.tab_button.name}")
    def update_tab_btn_last_clicked(self, event: Button.Pressed) -> None:
        self.query(Button).remove_class(Tcss.last_clicked.name)
        event.button.add_class(Tcss.last_clicked.name)
